# Task List: Advanced RAG Optimization & Self-Correcting Agentic System

- `[x]` 1. Requirements Update: Append torch, transformers, redis, and prometheus-client to requirements.txt
- `[x]` 2. PyTorch Accelerator Pipeline:
    - `[x]` Modify embedding.py to use raw torch, AutoTokenizer, and AutoModel with MPS/CUDA detection and Mean Pooling.
    - `[x]` Modify hybrid_retriever.py to use the new raw PyTorch embedding logic for queries.
- `[x]` 3. Redis Semantic Caching:
    - `[x]` Set up Redis client connection in api/app.py and fallback handlers.
    - `[x]` Implement semantic cache lookup inside the query pipeline.
- `[x]` 4. Self-Correcting LangGraph Loop:
    - `[x]` Add hallucination grader logic to generator.py.
    - `[x]` Add relevance grader logic to generator.py.
    - `[x]` Add query rewriter node.
    - `[x]` Update the StateGraph structure and add conditional edges.
- `[x]` 5. Observability & Infrastructure:
    - `[x]` Instrument FastAPI endpoints with Prometheus metrics (token counts, latencies, cache metrics).
    - `[x]` Update docker-compose.yml to launch Redis and Prometheus services.
