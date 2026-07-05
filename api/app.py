import os
import time
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.staticfiles import StaticFiles
from src.generator import Generator

app = FastAPI(
    title="KanonesKa - Outbound-India Travel Compliance RAG API",
    description="An advanced Hybrid RAG-based assistant for Indian outbound travelers using FAISS + BM25 + Cross-Encoder Reranking + Groq Llama-3 + LangGraph",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static frontend files
app.mount("/gui", StaticFiles(directory="frontend_react/dist", html=True), name="gui")

generator = Generator()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 10
    final_k: int = 3

class SourceInfo(BaseModel):
    chunk_id: int
    country: str
    category: str
    text: str
    rerank_score: float
    dense_score: float
    sparse_score: float

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    latency: float

@app.get("/")
def read_root():
    return {"message": "Welcome to the Outbound-India Travel Compliance RAG API!"}

@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    start_time = time.time()
    try:
        res = generator.ask(request.query, top_k=request.top_k, final_k=request.final_k)
        latency = time.time() - start_time
        return {
            "answer": res["answer"],
            "sources": res["sources"],
            "latency": round(latency, 3)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/countries")
def get_countries():
    import json
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "..", "data", "processed", "travel_data.json")
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

