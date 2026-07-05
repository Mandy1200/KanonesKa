# src/generator.py

import os
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

try:
    from hybrid_retriever import HybridRetriever
except ImportError:
    from .hybrid_retriever import HybridRetriever

# 🔐 Load environment variables from .env file
load_dotenv()

class RAGState(TypedDict):
    query: str
    retrieved_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    answer: str

class Generator:
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        """
        Initializes the Groq-based LLM, the retriever, and the LangGraph workflow.
        """
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        self.retriever = HybridRetriever(
            index_path=os.path.join(BASE_DIR, "data", "processed", "faiss_cosine_index.idx"),
            chunk_json_path=os.path.join(BASE_DIR, "data", "processed", "travel_chunks.json")
        )

        # Initialize Groq LLM via LangChain
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=0.2,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

        # Build stateful LangGraph workflow
        workflow = StateGraph(RAGState)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("rerank", self._rerank_node)
        workflow.add_node("generate", self._generate_node)

        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "generate")
        workflow.add_edge("generate", END)

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
        """Node for Cross-Encoder document reranking."""
        retrieved = state["retrieved_chunks"]
        if not retrieved:
            return {"reranked_chunks": []}
            
        query = state["query"]
        pairs = [[query, item["text"]] for item in retrieved]
        rerank_scores = self.retriever.reranker.predict(pairs)
        
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
        return {"answer": response.content}

    def ask(self, query: str, top_k: int = 10, final_k: int = 3) -> dict:
        """
        Invokes the stateful LangGraph pipeline.
        """
        # Run stategraph workflow
        result = self.graph.invoke({"query": query})
        
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("reranked_chunks", [])
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


