# KanonesKa: A Stateful Hybrid-RAG Travel Compliance & Flight Routing System
## Consolidating Systems Engineering & Information Retrieval Methodology (final_research_documentation.md)

**Author**: Lead Systems Architect & RAG Engineer  
**Scope**: Final Academic & Technical Synthesis  

---

## 📄 Abstract
KanonesKa is a stateful, hardware-accelerated **Hybrid Retrieval-Augmented Generation (Hybrid-RAG)** system designed to assist outbound Indian travelers with customs regulations, safety guidelines, and multi-leg flight logistics. The platform integrates a dense vector search index (FAISS FlatIP) with a sparse search index (BM25Okapi) using **Reciprocal Rank Fusion (RRF)**, reranked via a joint-attention **Cross-Encoder Model** running on device-level accelerators (MPS/CUDA). Flight paths are optimized dynamically across India's top 100 cities utilizing a modified **Dijkstra's algorithm**. User records and sessions are persisted to a cloud PostgreSQL database synchronized using **Supabase Auth & Row-Level Security (RLS)**. Telemetry is tracked in real-time using **Prometheus**.

---

## 🛠️ Complete System Architecture

```mermaid
graph TD
    Client([React Frontend]) -->|1. Auth & Sync| Supabase[(Supabase Cloud DB & Auth)]
    Client -->|2. Plan Request| API[FastAPI Server]
    
    subgraph Observability
        API -->|Prometheus Metrics| Prom[Prometheus Scraper]
    end
    
    subgraph Routing Engine
        API -->|3. Dijkstra Pathfinding| Router[Cheapest Flight Graph]
        Router -->|Top 100 Cities Map| Hubs{Primary Airport Hubs}
    end
    
    subgraph Advanced Retrieval Pipeline (RAG)
        API -->|4. Query Vectorization| PyTorch[Raw PyTorch Tokenizer]
        PyTorch -->|5. Mean Pooling & L2 Normalization| Device[GPU / MPS Accelerator]
        Device -->|6. Dense Search| FAISS[FAISS FlatIP Cosine Index]
        API -->|7. Sparse Search| BM25[BM25Okapi Keyword Corpus]
        FAISS & BM25 -->|8. Rank Fusion| RRF[Reciprocal Rank Fusion]
        RRF -->|9. Joint Attention Reranking| Cross[Cross-Encoder ms-marco-MiniLM]
    end
    
    subgraph Generation & Guardrails
        Cross -->|10. Grounded context| Groq[Groq Llama-3 API]
        Groq -->|Self-RAG feedback loop| LangGraph{LangGraph Orchestrator}
        LangGraph -->|Passes relevance check| Return[Grounded Itinerary Response]
    end
    
    Return -->|11. Send Itinerary + Photo URL| Client
```

---

## 1. 🔍 Advanced Information Retrieval (IR) Methodology

### A. Raw PyTorch Embedding & Mean Pooling (Dense Retrieval)
Rather than relying on high-level orchestration abstractions (which limit device-level memory optimizations), the system utilizes raw PyTorch for model inference. Query vectors are calculated on physical hardware accelerators (Apple Silicon `MPS` or NVIDIA `CUDA`):

$$\text{Embedding}(X) = \frac{\sum_{i=1}^{L} (T_i \times M_i)}{\sum_{i=1}^{L} M_i}$$

Where $T_i$ represents the hidden states of token $i$, and $M_i$ represents the binary attention mask value ($0$ or $1$) mapping token relevance. The generated hidden states are then $L_2$ normalized to ensure correct Cosine Similarity projections in flat vector space:

$$\text{Cosine}(A, B) = \frac{A \cdot B}{\|A\|\|B\|}$$

### B. BM25Okapi Keyword Indexing (Sparse Retrieval)
Exact keyword matches (crucial for terms like *"vaping legality"* or *"50g gold limits"*) are indexed via a sparse TF-IDF variant:

$$\text{Score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \times \frac{f(q_i, D) \times (k_1 + 1)}{f(q_i, D) + k_1 \times (1 - b + b \times \frac{|D|}{\text{avgdl}})}$$

Where $f(q_i, D)$ is the term frequency of query token $q_i$ in document $D$, $|D|$ is the document length, and $\text{avgdl}$ is the average document length across the corpus.

### C. Reciprocal Rank Fusion (RRF)
To merge candidates from sparse and dense distributions without score calibration issues, we implement Reciprocal Rank Fusion ($k = 60$):

$$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{60 + r_m(d)}$$

Where $M$ represents the search engines (FAISS and BM25), and $r_m(d)$ is the document rank in search engine $m$.

### D. Cross-Encoder Reranking
The top-10 fused candidates are evaluated jointly (query + document context) through a local **Cross-Encoder Model** (`cross-encoder/ms-marco-MiniLM-L-6-v2`) to capture deep attention interactions, selecting the top-3 most relevant grounded passages.

---

## 🛫 2. Shortest-Path Flight Routing Logic

The routing engine dynamically calculates outbound flight schedules from India's top 100 cities to gateway hubs:
*   **Fully Connected Hub Graph**: Programmatically generates connecting legs:
    $$\text{Local City} \xrightarrow{\text{Domestic}} \text{Nearest Indian Hub (DEL/BOM/CCU/BLR/BBI)} \xrightarrow{\text{International}} \text{Global Destination}$$
*   **Dijkstra cost Minimization**: Computes shortest pathways by minimizing travel cost.
*   **Priority Queue Tuple Safety**: To resolve comparison conflicts in python `heapq` when travel costs are identical, tuples utilize an incrementing sequence counter:
    $$\text{Priority Tuple} = (\text{Cost}, \text{Sequence Counter}, \text{Airport Code}, \text{Route List})$$

---

## 🔒 3. Session Security & Cloud DB Synchronization

We implement client-side Supabase JS SDK flows to manage user identity and database records:
*   **Authentication**: Standard Sign-Up requests **Username**, **Email**, and **Password**, registering the Username in the session's `user_metadata` dictionary. Login supports either Username or Email logins.
*   **Cloud PostgreSQL Sync**: Saved multi-leg itineraries are stored in the cloud PostgreSQL database under `saved_trips`.
*   **Row-Level Security (RLS)**: Protects all SQL operations by validating transactions using session UUIDs:
    ```sql
    create policy "Users can view their own trips"
    on public.saved_trips for select
    using (auth.uid() = user_id);
    ```
*   **Seamless Metadata Storage**: To prevent local table mutations, dynamic retrieval sources (BM25, FAISS, and Rerank scores) are packed directly into the `flight_route` JSONB field, ensuring backwards compatibility.

---

## 📈 4. Prometheus Observability Metrics

The server tracks metrics under `/metrics`:
*   `kanoneska_requests_total`: Counts incoming queries classified by HTTP response codes.
*   `kanoneska_semantic_cache_total`: Tracks semantic hits ($\ge 0.96$ similarity threshold) and misses.
*   `kanoneska_request_latency_seconds`: Precise distribution histograms mapping the latency of hybrid search and generation.
*   **Vite UI Badges**: Front-end renders dynamic latency markers and semantic cache hit indicators to confirm instantaneous cache checks.
