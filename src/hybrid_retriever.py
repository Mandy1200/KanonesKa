import os
import json
import faiss
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification
from rank_bm25 import BM25Okapi

# Set hardware acceleration device
device = torch.device(
    "cuda" if torch.cuda.is_available() 
    else "mps" if torch.backends.mps.is_available() 
    else "cpu"
)

class HybridRetriever:
    def __init__(self, index_path: str, chunk_json_path: str, embedding_model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', reranker_model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initializes the Hybrid (FAISS + BM25) Retriever using raw PyTorch inference on GPU/MPS/CPU.
        """
        # 1. Load Chunks
        if not os.path.exists(chunk_json_path):
            raise FileNotFoundError(f"Chunks file not found: {chunk_json_path}")
        with open(chunk_json_path, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
            
        # 2. Load FAISS Dense Index
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found: {index_path}")
        self.index = faiss.read_index(index_path)
        
        # 3. Load Embedding Model & Tokenizer on Device Accelerator
        self.embed_tokenizer = AutoTokenizer.from_pretrained(embedding_model_name)
        self.embed_model = AutoModel.from_pretrained(embedding_model_name).to(device)
        self.embed_model.eval()
        
        # 4. Initialize BM25 Sparse Index
        self.tokenized_corpus = [chunk["text"].lower().split() for chunk in self.chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        # 5. Load Cross-Encoder Reranker Model & Tokenizer on Device Accelerator
        print(f"Loading PyTorch Cross-Encoder Reranker on {device}: {reranker_model_name}...")
        self.rerank_tokenizer = AutoTokenizer.from_pretrained(reranker_model_name)
        self.rerank_model = AutoModelForSequenceClassification.from_pretrained(reranker_model_name).to(device)
        self.rerank_model.eval()
        print("Retriever initialization complete.")

    def dense_search(self, query: str, top_k: int = 10):
        """Perform semantic search using FAISS and raw PyTorch embeddings."""
        # Tokenize and execute forward pass on device
        encoded_input = self.embed_tokenizer([query], padding=True, truncation=True, return_tensors='pt').to(device)
        with torch.no_grad():
            model_output = self.embed_model(**encoded_input)
            
        # Mean Pooling to get sentence embeddings
        token_embeddings = model_output[0]
        attention_mask = encoded_input['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sentence_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        # L2 Normalize for cosine similarity matching
        query_vector = F.normalize(sentence_embeddings, p=2, dim=1).cpu().numpy()
        
        # FAISS search
        distances, indices = self.index.search(np.array(query_vector, dtype=np.float32), top_k)
        
        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], distances[0])):
            if idx != -1:
                results.append({
                    "chunk": self.chunks[idx],
                    "dense_score": float(score),
                    "dense_rank": rank + 1
                })
        return results

    def sparse_search(self, query: str, top_k: int = 10):
        """Perform keyword search using BM25."""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for rank, idx in enumerate(top_indices):
            score = scores[idx]
            if score > 0:
                results.append({
                    "chunk": self.chunks[idx],
                    "sparse_score": float(score),
                    "sparse_rank": rank + 1
                })
        return results

    def query(self, query_str: str, retrieve_k: int = 10, final_k: int = 3, rrf_constant: int = 60) -> list:
        """
        Runs Hybrid Retrieval + RRF + Cross-Encoder Reranking using raw PyTorch.
        """
        # Step A: Run Dense and Sparse Searches
        dense_results = self.dense_search(query_str, top_k=retrieve_k)
        sparse_results = self.sparse_search(query_str, top_k=retrieve_k)
        
        # Step B: Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        chunk_map = {}
        retrieval_metadata = {}
        
        for item in dense_results:
            cid = item["chunk"]["chunk_id"]
            chunk_map[cid] = item["chunk"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_constant + item["dense_rank"]))
            retrieval_metadata[cid] = {"dense_score": item["dense_score"], "dense_rank": item["dense_rank"]}
            
        for item in sparse_results:
            cid = item["chunk"]["chunk_id"]
            chunk_map[cid] = item["chunk"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_constant + item["sparse_rank"]))
            if cid not in retrieval_metadata:
                retrieval_metadata[cid] = {}
            retrieval_metadata[cid]["sparse_score"] = item["sparse_score"]
            retrieval_metadata[cid]["sparse_rank"] = item["sparse_rank"]

        # Sort candidate chunks by RRF score
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:retrieve_k]
        
        if not sorted_candidates:
            return []
            
        # Step C: Reranking with PyTorch Cross-Encoder
        candidate_chunks = [chunk_map[cid] for cid, _ in sorted_candidates]
        pairs = [[query_str, chunk["text"]] for chunk in candidate_chunks]
        
        # Tokenize and run cross-encoder prediction on accelerator device
        features = self.rerank_tokenizer(pairs, padding=True, truncation=True, return_tensors="pt").to(device)
        with torch.no_grad():
            model_output = self.rerank_model(**features)
            
        # Extract classification logits (squeezed to 1D)
        rerank_scores = model_output.logits.squeeze(-1).cpu().numpy()
        
        # If there's only one candidate, make sure rerank_scores is iterable
        if len(candidate_chunks) == 1:
            rerank_scores = [float(rerank_scores)]
        
        # Build list with all metadata
        reranked_results = []
        for i, chunk in enumerate(candidate_chunks):
            cid = chunk["chunk_id"]
            meta = retrieval_metadata[cid]
            reranked_results.append({
                "chunk_id": cid,
                "country": chunk["country"],
                "category": chunk["category"],
                "text": chunk["text"],
                "rerank_score": float(rerank_scores[i]),
                "dense_score": meta.get("dense_score", 0.0),
                "sparse_score": meta.get("sparse_score", 0.0)
            })
            
        # Sort by rerank score descending
        reranked_results = sorted(reranked_results, key=lambda x: x["rerank_score"], reverse=True)
        
        return reranked_results[:final_k]

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    retriever = HybridRetriever(
        index_path=os.path.join(BASE_DIR, "..", "data", "processed", "faiss_cosine_index.idx"),
        chunk_json_path=os.path.join(BASE_DIR, "..", "data", "processed", "travel_chunks.json")
    )
    test_query = "What is the gold limit for travelers entering India from Dubai?"
    results = retriever.query(test_query, final_k=3)
    print("\n--- TEST RETRIEVAL RESULTS ---")
    for r in results:
        print(f"[{r['country']} - {r['category']}] (Rerank Score: {r['rerank_score']:.4f})")
        print(f"Text: {r['text']}")
        print(f"FAISS Score: {r['dense_score']:.4f} | BM25 Score: {r['sparse_score']:.2f}")
        print("-" * 50)
