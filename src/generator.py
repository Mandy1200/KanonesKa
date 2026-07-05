# src/generator.py

import os
import torch
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

try:
    from hybrid_retriever import HybridRetriever
    from semantic_cache import SemanticCache
except ImportError:
    from .hybrid_retriever import HybridRetriever
    from .semantic_cache import SemanticCache

# Load environment variables
load_dotenv()

# Detect hardware acceleration device
device = torch.device(
    "cuda" if torch.cuda.is_available() 
    else "mps" if torch.backends.mps.is_available() 
    else "cpu"
)

class RAGState(TypedDict):
    query: str
    original_query: str
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    answer: str
    loop_count: int

class Generator:
    def __init__(self, model_name: str = "llama-3.1-8b-instant", redis_host='localhost', redis_port=6379):
        """
        Initializes the Groq LLM, the PyTorch retriever, the Semantic Cache, and the stateful LangGraph.
        """
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        # Initialize PyTorch Retriever
        self.retriever = HybridRetriever(
            index_path=os.path.join(BASE_DIR, "data", "processed", "faiss_cosine_index.idx"),
            chunk_json_path=os.path.join(BASE_DIR, "data", "processed", "travel_chunks.json")
        )

        # Initialize L1/L2 Semantic Cache
        redis_host_env = os.getenv("REDIS_HOST", redis_host)
        redis_port_env = int(os.getenv("REDIS_PORT", redis_port))
        self.cache = SemanticCache(redis_host=redis_host_env, redis_port=redis_port_env, similarity_threshold=0.96)

        # Initialize Groq LLM via LangChain
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=0.2,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

        # Build stateful LangGraph workflow with self-correction nodes
        workflow = StateGraph(RAGState)
        
        # Add Nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("rerank", self._rerank_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("rewrite", self._rewrite_query_node)

        # Build Connections & Edges
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "generate")
        
        # Add Conditional routing loop for self-correction (hallucinations/relevance check)
        workflow.add_conditional_edges(
            "generate",
            self._route_after_generation,
            {
                "rewrite": "rewrite",
                "end": END
            }
        )
        
        # After rewrite node, we query database again
        workflow.add_edge("rewrite", "retrieve")

        self.graph = workflow.compile()

    def _retrieve_node(self, state: RAGState) -> Dict[str, Any]:
        """Node for Dense + Sparse query retrieval & Reciprocal Rank Fusion."""
        query = state["query"]
        dense_res = self.retriever.dense_search(query, top_k=10)
        sparse_res = self.retriever.sparse_search(query, top_k=10)
        
        # RRF Score combining
        rrf_scores = {}
        chunk_map = {}
        retrieval_metadata = {}
        rrf_constant = 60
        
        for item in dense_res:
            cid = item["chunk"]["chunk_id"]
            chunk_map[cid] = item["chunk"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_constant + item["dense_rank"]))
            retrieval_metadata[cid] = {"dense_score": item["dense_score"], "dense_rank": item["dense_rank"]}
            
        for item in sparse_res:
            cid = item["chunk"]["chunk_id"]
            chunk_map[cid] = item["chunk"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (rrf_constant + item["sparse_rank"]))
            if cid not in retrieval_metadata:
                retrieval_metadata[cid] = {}
            retrieval_metadata[cid]["sparse_score"] = item["sparse_score"]
            retrieval_metadata[cid]["sparse_rank"] = item["sparse_rank"]
            
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        
        retrieved = []
        for cid, _ in sorted_candidates:
            chunk = chunk_map[cid]
            meta = retrieval_metadata[cid]
            retrieved.append({
                "chunk_id": cid,
                "country": chunk["country"],
                "category": chunk["category"],
                "text": chunk["text"],
                "dense_score": meta.get("dense_score", 0.0),
                "sparse_score": meta.get("sparse_score", 0.0)
            })
        return {"retrieved_chunks": retrieved}

    def _rerank_node(self, state: RAGState) -> Dict[str, Any]:
        """Node for raw PyTorch Cross-Encoder document reranking on MPS/CUDA GPU device."""
        retrieved = state["retrieved_chunks"]
        if not retrieved:
            return {"reranked_chunks": []}
            
        query = state["query"]
        pairs = [[query, item["text"]] for item in retrieved]
        
        # Run raw PyTorch cross-encoder tokenization & classification
        features = self.retriever.rerank_tokenizer(pairs, padding=True, truncation=True, return_tensors="pt").to(device)
        with torch.no_grad():
            model_output = self.retriever.rerank_model(**features)
            
        rerank_scores = model_output.logits.squeeze(-1).cpu().numpy()
        
        if len(retrieved) == 1:
            rerank_scores = [float(rerank_scores)]
            
        for i, item in enumerate(retrieved):
            item["rerank_score"] = float(rerank_scores[i])
            
        reranked = sorted(retrieved, key=lambda x: x["rerank_score"], reverse=True)[:3]
        return {"reranked_chunks": reranked}

    def _generate_node(self, state: RAGState) -> Dict[str, Any]:
        """Node for formatted response generation grounded in retrieved context."""
        reranked = state["reranked_chunks"]
        if not reranked:
            return {"answer": "I'm sorry, I couldn't find any relevant travel rules for your query. Please specify a country or rephrase your question."}
            
        context = "\n\n".join([chunk["text"] for chunk in reranked])
        messages = [
            SystemMessage(
                content=(
                    "You are a specialized Outbound-India Travel Compliance Assistant. "
                    "Your role is to help Indian citizens travel safely and comply with laws outside India.\n\n"
                    "RULES:\n"
                    "1. Rely ONLY on the provided context to answer the user's question. Do not speculate or use outside knowledge.\n"
                    "2. If the context does not contain enough information to answer the question, state politely that the information is not available in the travel rules database.\n"
                    "3. Highlight critical safety procedures, local customs, gold limits (₹ or grams), duty-free allowances, and emergency contacts when relevant.\n"
                    "4. Maintain an official, neutral, and helpful tone."
                )
            ),
            HumanMessage(
                content=f"Context:\n{context}\n\nQuestion: {state['query']}"
            )
        ]
        response = self.llm.invoke(messages)
        
        # Track loop loops
        current_loops = state.get("loop_count", 0)
        return {"answer": response.content, "loop_count": current_loops + 1}

    def _rewrite_query_node(self, state: RAGState) -> Dict[str, Any]:
        """Query rewriter node to optimize query context parameters."""
        print(f"🔄 Rewriting query to optimize database retrieval (Loop count: {state['loop_count']}).")
        messages = [
            SystemMessage(content=(
                "You are an AI query rewriter. Rewrite the user's query to optimize it for a database search, focusing heavily on country compliance terms and travel rules.\n"
                "Return ONLY the rewritten query text. Do not add explanations, titles, or quotes."
            )),
            HumanMessage(content=f"Rewrite this query: {state['query']}")
        ]
        rewritten = self.llm.invoke(messages).content.strip()
        print(f"Original: '{state['query']}' -> Rewritten: '{rewritten}'")
        return {"query": rewritten}

    def _route_after_generation(self, state: RAGState) -> str:
        """
        Grades the generation for hallucinations and relevance.
        Decides whether to route to END or loop back via rewrite.
        """
        if state.get("loop_count", 0) >= 2:
            print("⚠️ Max correction iterations reached. Routing to END to prevent infinite loops.")
            return "end"

        # 1. Hallucination Check
        context = "\n\n".join([chunk["text"] for chunk in state["reranked_chunks"]])
        messages = [
            SystemMessage(content=(
                "You are a strict AI safety grader. Assess whether the generated answer is fully grounded in and supported by the retrieved documents.\n"
                "Respond with EXACTLY one word: 'yes' or 'no'. Do not include explanations, quotes, or punctuation."
            )),
            HumanMessage(content=f"Retrieved Documents:\n{context}\n\nGenerated Answer:\n{state['answer']}")
        ]
        try:
            grade = self.llm.invoke(messages).content.strip().lower()
            if "no" in grade:
                print("❌ Grader: Answer contains hallucinations or ungrounded data. Triggering self-correction loop.")
                return "rewrite"
        except Exception as e:
            print(f"Hallucination grading error: {e}")

        # 2. Relevance Check
        messages = [
            SystemMessage(content=(
                "You are an AI relevance grader. Assess whether the generated answer directly addresses the user's question.\n"
                "Respond with EXACTLY one word: 'yes' or 'no'. Do not include explanations, quotes, or punctuation."
            )),
            HumanMessage(content=f"User Question:\n{state['original_query']}\n\nGenerated Answer:\n{state['answer']}")
        ]
        try:
            grade = self.llm.invoke(messages).content.strip().lower()
            if "no" in grade:
                print("❌ Grader: Answer does not resolve user query. Triggering self-correction loop.")
                return "rewrite"
        except Exception as e:
            print(f"Relevance grading error: {e}")

        print("✅ Grader: Generation passed all safety and relevance checks.")
        return "end"

    def ask(self, query: str, top_k: int = 10, final_k: int = 3) -> dict:
        """
        Invokes semantic cache checks and, on cache-miss, executes LangGraph self-correction pipelines.
        """
        # A: Check L1/L2 Semantic Cache
        cached_res = self.cache.check(query)
        if cached_res:
            return cached_res

        # B: Execute LangGraph
        result = self.graph.invoke({
            "query": query,
            "original_query": query,
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "answer": "",
            "loop_count": 0
        })
        
        answer = result.get("answer", "")
        sources = result.get("reranked_chunks", [])

        # C: Store in L1/L2 Semantic Cache for future queries
        if answer and sources:
            self.cache.set(query, answer, sources)

        return {
            "answer": answer,
            "sources": sources,
            "cached": False
        }

if __name__ == "__main__":
    generator = Generator()
    query = "What is the gold jewelry limit for traveling to UAE?"
    res = generator.ask(query)
    print("\nAnswer:\n")
    print(res["answer"])
    print("\nSources:\n")
    for s in res["sources"]:
        print(f"- {s['country']} ({s['category']}): Rerank Score {s['rerank_score']:.4f}")
