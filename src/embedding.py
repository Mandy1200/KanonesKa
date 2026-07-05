import os
import json
import faiss
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# Detect hardware acceleration device (MPS for Mac, CUDA for NVIDIA GPU, CPU otherwise)
device = torch.device(
    "cuda" if torch.cuda.is_available() 
    else "mps" if torch.backends.mps.is_available() 
    else "cpu"
)
print(f"Embedding Pipeline using device accelerator: {device}")

def load_chunks(json_path: str):
    """Loads text chunks from a JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_embeddings(texts: list[str], model_name='sentence-transformers/all-MiniLM-L6-v2') -> np.ndarray:
    """Generates normalized embeddings using raw PyTorch tokenization and model inference on GPU/MPS/CPU."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name).to(device)
    model.eval()

    all_embeddings = []
    
    # Process in batches to manage memory
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        
        # Tokenize and place tensors on GPU/MPS device
        encoded_input = tokenizer(batch_texts, padding=True, truncation=True, return_tensors='pt').to(device)
        
        with torch.no_grad():
            model_output = model(**encoded_input)
            
        # Perform custom Mean Pooling
        token_embeddings = model_output[0]  # First element contains all token embeddings
        attention_mask = encoded_input['attention_mask']
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        sentence_embeddings = sum_embeddings / sum_mask
        
        # Normalize embeddings to unit length (cosine similarity)
        normalized_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
        
        # Move back to CPU and convert to numpy
        all_embeddings.append(normalized_embeddings.cpu().numpy())
        
    return np.vstack(all_embeddings)

def save_faiss_index(embeddings: np.ndarray, output_path: str):
    """Saves normalized embeddings to a FAISS index file using cosine similarity."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, output_path)
    print(f"FAISS index (cosine similarity) saved to {output_path}")


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    chunk_path = os.path.join(BASE_DIR, "..", "data", "processed", "travel_chunks.json")
    index_path = os.path.join(BASE_DIR, "..", "data", "processed", "faiss_cosine_index.idx")

    chunks = load_chunks(chunk_path)
    texts = [chunk["text"] for chunk in chunks]

    embeddings = generate_embeddings(texts)
    save_faiss_index(embeddings, index_path)
