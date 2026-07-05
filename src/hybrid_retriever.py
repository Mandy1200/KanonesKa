import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi

class HybridRetriever:
    def __init__(self, index_path: str, chunk_json_path: str, embedding_model_name: str = 'all-MiniLM-L6-v2', reranker_model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """
        Initializes the Hybrid (FAISS + BM25) Retriever with a Cross-Encoder Reranker.
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
        
        # 3. Load Embedding Model
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # 4. Initialize BM25 Sparse Index
        # Simple tokenization by splitting words and converting to lowercase
        self.tokenized_corpus = [chunk["text"].lower().split() for chunk in self.chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        
        # 5. Load Cross-Encoder Reranker
        print(f"Loading Cross-Encoder Reranker: {reranker_model_name}...")
        self.reranker = CrossEncoder(reranker_model_name)
        print("Retriever initialization complete.")

    def dense_search(self, query: str, top_k: int = 10):
        """Perform semantic search using FAISS."""
        query_vector = self.embedding_model.encode([query])
        faiss.normalize_L2(query_vector)
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
            if score > 0:  # Only count documents with some matching terms
                results.append({
                    "chunk": self.chunks[idx],
                    "sparse_score": float(score),
                    "sparse_rank": rank + 1
                })
        return results

    def query(self, query_str: str, retrieve_k: int = 10, final_k: int = 3, rrf_constant: int = 60) -> list:
        """
        Runs Hybrid Retrieval + RRF + Cross-Encoder Reranking.
        """
        # Step A: Run Dense and Sparse Searches
        dense_results = self.dense_search(query_str, top_k=retrieve_k)
        sparse_results = self.sparse_search(query_str, top_k=retrieve_k)
        
        # Step B: Reciprocal Rank Fusion (RRF)
        rrf_scores = {}  # chunk_id -> score
        chunk_map = {}   # chunk_id -> chunk
        retrieval_metadata = {} # chunk_id -> source details
        
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
            
        # Step C: Reranking with Cross-Encoder
        candidate_chunks = [chunk_map[cid] for cid, _ in sorted_candidates]
        pairs = [[query_str, chunk["text"]] for chunk in candidate_chunks]
        
        rerank_scores = self.reranker.predict(pairs)
        
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
        
        # Return top final_k
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
