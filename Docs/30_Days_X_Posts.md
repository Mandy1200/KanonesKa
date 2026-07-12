# KanonesKa: 30 Days "Build in Public" X (Twitter) Strategy

Here is a complete 30-day post schedule to share your journey of building KanonesKa from scratch. Each post is optimized for X (Twitter), keeping it under 280 characters where possible, or formatted as a concise thread hook. It highlights your advanced systems engineering, IR math, and full-stack development skills.

---

### **Day 1: The Problem & The Vision**
I’m building KanonesKa: a stateful Hybrid-RAG travel compliance & flight routing system for Indian citizens traveling abroad. Ever struggled with changing visa rules, gold limits, or safety guidelines? I’m solving this with AI. Follow along for 30 days! 🚀
#BuildInPublic #AI #TravelTech #RAG

### **Day 2: Designing the Architecture**
System design day! KanonesKa will feature:
1️⃣ Hybrid RAG (FAISS + BM25 + RRF)
2️⃣ Dijkstra Flight Path Router
3️⃣ Stateful React Wizard
4️⃣ Supabase Auth & Cloud Sync
Time to turn this whiteboard sketch into reality. 🛠️
#SystemDesign #BuildInPublic #Engineering

### **Day 3: Tech Stack Selection**
Why settle for generic wrappers? My stack for KanonesKa:
Backend: FastAPI, Raw PyTorch (MPS/CUDA), Groq (Llama-3)
Frontend: React (Vite)
Database: Supabase (PostgreSQL) + FAISS + Redis
Observability: Prometheus
Building for extreme low latency. ⚡
#TechStack #Python #WebDev

### **Day 4: Data Ingestion & Structuring**
Data is the lifeblood of RAG. Today, I built the ingestion pipeline to parse customs regulations, visa fees, and safety parameters for 55 countries into structured JSON. Clean data = zero LLM hallucinations later. 🧹
#DataEngineering #BuildInPublic #AI

### **Day 5: Raw PyTorch Embeddings**
Skipping the heavy abstractions today! I wrote a custom PyTorch pipeline for sentence embeddings using Mean Pooling and L2 Normalization directly on the hardware accelerator (MPS/CUDA). The performance boost is insane. 🔥
#PyTorch #MachineLearning #BuildInPublic

### **Day 6: Building the FAISS Index (Dense Retrieval)**
Implemented a local FAISS FlatIP index for semantic search. It checks query vectors against the database in sub-milliseconds using C++ bindings. Dense retrieval is incredibly fast! 🏎️
#VectorDatabase #FAISS #BuildInPublic #AI

### **Day 7: The Keyword Problem (BM25 Sparse Retrieval)**
Dense vectors are great, but they suck at exact keyword matching (like "50g gold" or "vape"). Today, I added a BM25Okapi sparse index to run in parallel with FAISS. Zero hallucinations on specific laws now! ⚖️
#SearchEngine #InformationRetrieval #BuildInPublic

### **Day 8: Reciprocal Rank Fusion (RRF)**
How do you combine scores from FAISS (semantic) and BM25 (keyword)? Math! 🧮 
I implemented Reciprocal Rank Fusion (RRF) today to elegantly merge the two ranking distributions. Best of both worlds! 🌍
#Algorithms #BuildInPublic #AI

### **Day 9: Cross-Encoder Reranking**
To achieve production-grade RAG, I added a Cross-Encoder (ms-marco-MiniLM) to rerank the top 10 fused candidates. It evaluates the query and document *jointly* via attention mechanisms. The accuracy is mind-blowing! 🤯
#NLP #MachineLearning #BuildInPublic

### **Day 10: L1/L2 Semantic Caching**
Why compute the same embeddings twice? Today I built a dual-layer Semantic Cache: L1 (In-Memory Lists) and L2 (Redis). If a query has ≥0.96 cosine similarity to a past query, it resolves instantly. ⚡
#Redis #Backend #Optimization #BuildInPublic

### **Day 11: The Flight Routing Problem**
Travel planning isn't just about rules; it's about logistics. Today I started building a dynamic graph mapping India's top 100 cities to gateway hubs and 55 international destinations. Time to tackle graph algorithms! 🗺️
#GraphTheory #BuildInPublic #Coding

### **Day 12: Implementing Dijkstra’s Algorithm**
Algorithms in production! 💻 I wrote a custom Dijkstra shortest-path pathfinder to resolve the cheapest sequence of flights across my city graph in under 10ms. Big O notation matters in the real world!
#Algorithms #ComputerScience #BuildInPublic

### **Day 13: Heapq Conflict Resolution**
Python's `heapq` threw type errors when two flight routes had the exact same cost. The fix? I added an incrementing unique sequence counter to the priority tuple: (cost, counter, airport). Problem solved elegantly! 🐛🔨
#Python #Debugging #BuildInPublic

### **Day 14: Integrating LLMs (Groq + Llama-3)**
Time to generate text! I integrated Groq's ultra-fast LPU inference engine running Llama-3. It processes the retrieved RAG context and user profiles to generate structured itineraries in milliseconds! 🦙
#LLM #GenerativeAI #BuildInPublic

### **Day 15: Grounded Prompt Engineering**
LLMs hallucinate if you let them. Today I injected the retrieved RAG context (FAISS+BM25) directly into the system prompt. Now, the itinerary generation is strictly grounded in actual travel laws and customs rules! 🛡️
#PromptEngineering #AI #BuildInPublic

### **Day 16: Building the LangGraph Workflow**
Simple RAG isn't enough. Today I wrapped the backend in a stateful LangGraph workflow. It manages the retrieval, fusion, reranking, and generation as discrete, observable nodes. 🏗️
#LangChain #LangGraph #BuildInPublic #AI

### **Day 17: Self-Correction Loops (Self-RAG)**
Added a "Hallucination Grader" node to my LangGraph today. If the LLM generates an answer not supported by the context, the graph catches it, rewrites the query, and loops back to retrieve better data! 🔁
#AgenticAI #MachineLearning #BuildInPublic

### **Day 18: Unsplash API Integration**
Text is boring. I integrated the Unsplash API to dynamically fetch gorgeous landscape imagery matching the destination. Built a custom Markdown regex parser to render it beautifully in the final itinerary. 📸
#API #WebDev #BuildInPublic

### **Day 19: Starting the React Frontend**
Backend is solid; time for the UI! Initialized a Vite + React project today. Setting up the folder structure, global CSS tokens, and planning the component hierarchy for the travel wizard. ⚛️
#ReactJS #Frontend #BuildInPublic

### **Day 20: Glassmorphic UI Design**
Today was all about aesthetics. I implemented a stunning Glassmorphism design system for KanonesKa—translucent cards, soft gradients, and subtle micro-animations. It looks incredibly premium! ✨
#CSS #UIUX #WebDesign #BuildInPublic

### **Day 21: Stateful Multi-Step Wizard**
Built a custom React state machine today to handle the multi-leg wizard prompts: Origin ➔ Destination ➔ Traveler Profile ➔ Duration. Clean state management makes complex flows feel effortless! 🔄
#ReactJS #FrontendDev #BuildInPublic

### **Day 22: Split-Screen Auth Landing Page**
First impressions matter. Designed a sleek split-screen landing page. Left side: a glowing animated travel route card. Right side: dynamic login/register credential tabs. It’s coming together! 🎨
#WebDevelopment #Design #BuildInPublic

### **Day 23: Supabase Authentication Setup**
Security day! I integrated the Supabase JS SDK. Users can now register with a Username & Email, and login accepts either credential dynamically. I even added an inline click-to-edit username badge! 🔐
#Supabase #Auth #BuildInPublic

### **Day 24: Cloud PostgreSQL Sync**
Goodbye local storage! Wired the React frontend to save generated multi-leg itineraries directly to a cloud PostgreSQL database hosted on Supabase. Data is now persistent across sessions! ☁️
#PostgreSQL #Database #BuildInPublic

### **Day 25: Row-Level Security (RLS)**
You can never be too secure. Today I wrote SQL Row-Level Security (RLS) policies in Supabase. Now, database operations (SELECT/INSERT/DELETE) strictly validate the authenticated user's UUID. 🛡️
#CyberSecurity #SQL #BuildInPublic

### **Day 26: Storing RAG Sources in JSONB**
How do you save complex RAG metadata without breaking SQL schemas? I serialized the retrieved sources (dense/sparse scores) directly into a JSONB column payload. Fully backward compatible! 📦
#PostgreSQL #Engineering #BuildInPublic

### **Day 27: Exposing Metrics with Prometheus**
Production apps need observability. I integrated Prometheus `Counter` and `Histogram` metrics to track API latencies, cache hits, and request statuses. Exposing them on a `/metrics` target! 📈
#DevOps #Prometheus #BuildInPublic

### **Day 28: Visual Score Inspection Modal**
Transparency in AI is key. Today I built a fullscreen modal overlay in React that displays the exact Retrieval metrics (Rerank, Dense, and Sparse scores) for the documents that grounded the LLM's response! 📊
#Transparency #AI #BuildInPublic

### **Day 29: Final Integrations & Testing**
The final stretch! Today was spent squashing bugs, ensuring the UI is fully responsive across devices, and running load tests on the PyTorch inference pipeline. Everything is green! ✅
#SoftwareTesting #QA #BuildInPublic

### **Day 30: Launch Day! 🚀**
After 30 days of building in public, KanonesKa is complete! 
A stateful, hardware-accelerated, Hybrid-RAG travel compliance system with Dijkstra flight routing and cloud sync. 
Check out the architecture and code below! 👇
#Launch #BuildInPublic #AI #SaaS
