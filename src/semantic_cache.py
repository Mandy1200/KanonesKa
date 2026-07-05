import redis
import json
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# Set hardware acceleration device
device = torch.device(
    "cuda" if torch.cuda.is_available() 
    else "mps" if torch.backends.mps.is_available() 
    else "cpu"
)

class SemanticCache:
    def __init__(self, redis_host='localhost', redis_port=6379, similarity_threshold=0.96, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.threshold = similarity_threshold
        
        # 1. Connect to Redis (L2 Cache)
        try:
            self.redis = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True, socket_connect_timeout=2)
            self.redis.ping()
            self.redis_online = True
            print("Connected to Redis L2 Cache.")
        except Exception as e:
            self.redis_online = False
            print(f"Redis L2 Cache offline: {e}. Running in memory-only (L1) mode.")
            
        # 2. Local Embedding Model for Query Mapping (Raw PyTorch on Accelerator)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(device)
        self.model.eval()
        
        # 3. L1 Cache (In-Memory Index)
        self.l1_queries = []   # list of query strings
        self.l1_vectors = []   # list of numpy arrays
        self.l1_data = {}      # query -> {"answer": str, "sources": list}
        
        # 4. Hydrate L1 from Redis
        if self.redis_online:
            self.hydrate_l1()

    def hydrate_l1(self):
        try:
            keys = self.redis.keys("semcache:*")
            for k in keys:
                raw_data = self.redis.get(k)
                if raw_data:
                    data = json.loads(raw_data)
                    query = k.replace("semcache:", "")
                    vector = np.array(data["vector"], dtype=np.float32)
                    
                    self.l1_queries.append(query)
                    self.l1_vectors.append(vector)
                    self.l1_data[query] = {
                        "answer": data["answer"],
                        "sources": data["sources"]
                    }
            print(f"Hydrated L1 Cache with {len(self.l1_queries)} entries from Redis.")
        except Exception as e:
            print(f"Error hydrating L1 Cache: {e}")

    def embed_query(self, query: str) -> np.ndarray:
        encoded_input = self.tokenizer([query], padding=True, truncation=True, return_tensors='pt').to(device)
        with torch.no_grad():
            model_output = self.model(**encoded_input)
            
        token_embeddings = model_output[0]
        attention_mask = encoded_input['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sentence_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        
        normalized_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        return normalized_embeddings.cpu().numpy()[0]

    def check(self, query: str):
        """Checks if a semantically similar query exists in L1 cache."""
        if not self.l1_queries:
            return None
            
        # Compute embedding of incoming query
        query_vector = self.embed_query(query)
        
        # Compute cosine similarities with all L1 vectors
        similarities = []
        for v in self.l1_vectors:
            sim = np.dot(query_vector, v) / (np.linalg.norm(query_vector) * np.linalg.norm(v))
            similarities.append(sim)
            
        if not similarities:
            return None
            
        max_idx = np.argmax(similarities)
        max_sim = similarities[max_idx]
        
        if max_sim >= self.threshold:
            matched_query = self.l1_queries[max_idx]
            print(f"🚀 SEMANTIC CACHE HIT (Similarity: {max_sim:.4f}) for: '{matched_query}'")
            return {
                "answer": self.l1_data[matched_query]["answer"],
                "sources": self.l1_data[matched_query]["sources"],
                "cached": True,
                "similarity": float(max_sim)
            }
            
        return None

    def set(self, query: str, answer: str, sources: list):
        """Saves a new entry in both L1 (Memory) and L2 (Redis) Cache."""
        query_vector = self.embed_query(query)
        vector_list = query_vector.tolist()
        
        # Update L1
        self.l1_queries.append(query)
        self.l1_vectors.append(query_vector)
        self.l1_data[query] = {
            "answer": answer,
            "sources": sources
        }
        
        # Update L2 (Redis)
        if self.redis_online:
            try:
                cache_key = f"semcache:{query}"
                payload = json.dumps({
                    "vector": vector_list,
                    "answer": answer,
                    "sources": sources
                })
                self.redis.set(cache_key, payload)
            except Exception as e:
                print(f"Error writing to Redis L2: {e}")

if __name__ == "__main__":
    cache = SemanticCache(similarity_threshold=0.95)
    print("Testing cache...")
    cache.set("What is the visa rule for United Arab Emirates?", "Indian citizens with valid US visa get Visa on Arrival.", [])
    hit = cache.check("Visa requirements for UAE?")
    print(f"Cache lookup result: {hit}")
