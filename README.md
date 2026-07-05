# KanonesKa: Outbound-India Travel Compliance RAG Assistant

An advanced, hardware-accelerated **Hybrid Retrieval-Augmented Generation (Hybrid-RAG)** system and stateful planning wizard designed for Indian citizens traveling outbound.

KanonesKa evaluates visa rules, gold limits, duty-free caps, local customs, and safety guidelines across 55 destinations, offering optimized multi-leg flight routing and secure cloud-synced travel histories.

---

## 🚀 Key Features

1.  **State-of-the-Art Hybrid RAG Search**:
    *   **Dense Retrieval**: Uses raw PyTorch to compute text hidden states and mean pooling directly on hardware accelerators (`MPS`/`CUDA`). Search runs via a flat cosine similarity index (`faiss`).
    *   **Sparse Retrieval**: BM25Okapi keyword index targeting exact regulatory queries (e.g., *"vape legality"* or *"50g gold"*).
    *   **Rank Fusion**: Reciprocal Rank Fusion (RRF) merges dense and sparse results.
    *   **Cross-Encoder Reranking**: Evaluates query/document relevance jointly using a `ms-marco-MiniLM` transformer.
2.  **Stateful Multi-Step Planning Wizard**:
    *   Walks travelers through Starting City ➔ Target Destination ➔ Profile Select (Solo Female, Family, Couple, Duo) ➔ Trip Duration Days.
    *   Dynamically maps connecting flight legs from any of **India's top 100 cities** using **Dijkstra's shortest path** algorithm.
3.  **Supabase Auth & Cloud Database Sync**:
    *   Split-screen Auth page featuring animated travel route maps and clean Login/Register credential tabs.
    *   Saves and synchronizes multi-leg travel itineraries to a Supabase PostgreSQL instance secured with Row-Level Security (RLS).
4.  **Prometheus Metric Scraper**:
    *   Exposes system health indicators, request count classifications, and RAG latencies on a `/metrics` target endpoint.

---

## 📁 Repository Structure

```plaintext
KanonesKa/
├── api/
│   └── app.py               # FastAPI backend endpoints (/ask, /plan, /metrics)
├── src/
│   ├── hybrid_retriever.py  # BM25 + FAISS flat index search with RRF & Rerankers
│   ├── flight_router.py     # Dijkstra pathfinder for India's top 100 cities
│   ├── generator.py         # Stateful LangGraph RAG workflow & Groq bindings
│   ├── semantic_cache.py    # L1 (Memory) / L2 (Redis) vector similarity caching
│   └── unsplash_helper.py   # Destination cover photo scraper
├── frontend_react/
│   ├── src/
│   │   ├── App.jsx          # React wizard client, auth screens, modal triggers
│   │   ├── App.css          # Glassmorphic layout styling
│   │   └── supabaseClient.js# Supabase JS SDK client initializations
│   └── package.json
├── Docs/
│   ├── doc2.md              # Phase 2 documentation (PyTorch vector caches)
│   ├── doc3.md              # Phase 3 documentation (Wizard routing systems)
│   ├── doc4.md              # Phase 4 documentation (Grounded RAG integrations)
│   └── final_research_documentation.md # Academic-grade consolidated summary
├── requirements.txt         # Python dependencies
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
*   Python 3.11+
*   Node.js 18+ (for building React frontend)

### 2. Python Environment Setup
```bash
# Clone the repository
git clone https://github.com/Mandy1200/KanonesKa.git
cd KanonesKa

# Create virtual environment and activate
python -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Frontend Client Setup
```bash
cd frontend_react
npm install
npm run build
cd ..
```

---

## 🔑 Environment Configuration

Create a secure `.env` file at the repository root:

```env
GROQ_API_KEY=your_groq_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
```

---

## 🛢️ Supabase Database Configurations

Run the following SQL commands in your **[Supabase SQL Editor](https://supabase.com/dashboard/project/kwozfcivubtkjzcezlum/sql)** to initialize the RLS-secured schema:

```sql
create table public.saved_trips (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users(id) on delete cascade not null,
    origin text not null,
    destination text not null,
    profile text not null,
    days integer not null,
    itinerary text not null,
    photo_url text not null,
    flight_route jsonb not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

alter table public.saved_trips enable row level security;

create policy "Users can insert their own trips" on public.saved_trips for insert with check (auth.uid() = user_id);
create policy "Users can view their own trips" on public.saved_trips for select using (auth.uid() = user_id);
create policy "Users can delete their own trips" on public.saved_trips for delete using (auth.uid() = user_id);
```

---

## 🏃 Running the Application

### 1. Start the API Server
Start the Uvicorn FastAPI server from the repository root:
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access the Application Dashboard
Open your browser and navigate to:
👉 **[http://localhost:8000/gui](http://localhost:8000/gui)**
