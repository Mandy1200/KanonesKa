import os
import time
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi.staticfiles import StaticFiles
from src.generator import Generator
from src.flight_router import find_cheapest_flights, resolve_city_to_code, CODE_TO_CITY
from src.unsplash_helper import get_city_photo
from prometheus_client import Counter, Histogram, make_asgi_app
from langchain_core.messages import HumanMessage, SystemMessage

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

# 📈 Prometheus Observability Metrics
REQUEST_COUNT = Counter(
    "kanoneska_requests_total", 
    "Total number of requests handled by the API", 
    ["endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "kanoneska_request_latency_seconds", 
    "Time spent processing RAG requests", 
    ["endpoint"]
)
CACHE_METRIC = Counter(
    "kanoneska_semantic_cache_total", 
    "Semantic cache hits and misses count", 
    ["status"]
)

# Initialize generator instance
generator = Generator()

# Mount the static frontend files
app.mount("/gui", StaticFiles(directory="frontend_react/dist", html=True), name="gui")

# Mount Prometheus metrics app to /metrics
metrics_asgi_app = make_asgi_app()
app.mount("/metrics", metrics_asgi_app)

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
    cached: bool

class PlanRequest(BaseModel):
    origin: str
    destination: str
    profile: str
    days: int

class PlanResponse(BaseModel):
    origin: str
    destination: str
    profile: str
    days: int
    flight_route: Dict[str, Any]
    itinerary: str
    photo_url: str
    latency: float
    sources: List[SourceInfo]

@app.get("/")
def read_root():
    return {"message": "Welcome to the Outbound-India Travel Compliance RAG API!"}

@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    start_time = time.time()
    try:
        res = generator.ask(request.query, top_k=request.top_k, final_k=request.final_k)
        latency = time.time() - start_time
        
        # Track metrics
        REQUEST_COUNT.labels(endpoint="/ask", status_code="200").inc()
        REQUEST_LATENCY.labels(endpoint="/ask").observe(latency)
        
        is_cached = res.get("cached", False)
        if is_cached:
            CACHE_METRIC.labels(status="hit").inc()
        else:
            CACHE_METRIC.labels(status="miss").inc()

        return {
            "answer": res["answer"],
            "sources": res["sources"],
            "latency": round(latency, 3),
            "cached": is_cached
        }
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/ask", status_code="500").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan", response_model=PlanResponse)
def plan_trip(request: PlanRequest):
    start_time = time.time()
    try:
        # 1. Run Dijkstra Flight Pathfinder
        flight_res = find_cheapest_flights(request.origin, request.destination)
        if "error" in flight_res:
            raise HTTPException(status_code=400, detail=flight_res["error"])
            
        # 2. Fetch destination photo from Unsplash
        photo_url = get_city_photo(request.destination)
        
        # 3. Fetch Country Compliance Database
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(BASE_DIR, "..", "data", "processed", "travel_data.json")
        with open(db_path, "r", encoding="utf-8") as f:
            countries_db = json.load(f)
            
        # Match destination city to country record
        matched_country = None
        for c in countries_db:
            cities_lower = [city.lower() for city in c.get("cities", [])]
            if request.destination.lower() in cities_lower or request.destination.lower() == c["country"].lower():
                matched_country = c
                break
                
        if not matched_country:
            # Fallback to general destination RAG rules
            matched_country = {
                "country": request.destination,
                "local_currency_code": "USD",
                "cash_vs_card_reliance": "Varies",
                "solo_female_safety_rating": "Moderate",
                "vaping_e_cigarette_legality": "Varies",
                "primary_ride_hailing_apps": "Taxi / Grab",
                "tap_water_potable": False
            }
            
        # 4. Build Flight Details Text
        flight_details_list = []
        for segment in flight_res["route"]:
            flight_details_list.append(
                f"- {segment['from']} ➔ {segment['to']} via {segment['airline']} ({segment['flight_no']}) | Dep: {segment['dep']} | Arr: {segment['arr']} | {segment['duration']}"
            )
        flight_details_str = "\n".join(flight_details_list)
        
        # Run Hybrid RAG Retrieval (FAISS + BM25 + Cross-Encoder Reranking)
        try:
            rag_results = generator.retriever.query(
                f"What are the travel safety rules, customs limits, visa fees, and vaping regulations in {request.destination}?",
                final_k=3
            )
        except Exception as re:
            print(f"RAG retrieval fallback: {re}")
            rag_results = []

        rag_context_list = []
        for r in rag_results:
            rag_context_list.append(f"[{r['country']} - {r['category']}]: {r['text']}")
        rag_context_str = "\n\n".join(rag_context_list) if rag_context_list else "No specific context retrieved."

        # 5. Format LLM Itinerary Prompt
        system_prompt = (
            f"You are a specialized Travel Planning AI Agent. Your role is to generate a custom {request.days}-day travel itinerary "
            "for an Indian citizen traveling outbound, matching their traveler profile (e.g. family, couple, duo, solo female).\n"
            "RULES:\n"
            "1. Enforce strict safety warnings, transportation protocols, local laws, and currency guides based on the provided compliance parameters.\n"
            "2. Keep the formatting clean, elegant, and highly structured in Markdown.\n"
            "3. Embed the provided landscape photo URL at the very top of the markdown response in a centered/large format."
        )
        
        user_prompt = f"""Generate a {request.days}-day travel itinerary for a traveler with the profile '{request.profile}' traveling from '{request.origin}' to '{request.destination}'.

Destination Compliance & Safety Parameters:
- Country: {matched_country.get('country')}
- Currency Code: {matched_country.get('local_currency_code')} ({matched_country.get('cash_vs_card_reliance')})
- Solo Female Safety Rating: {matched_country.get('solo_female_safety_rating')}
- Vaping regulations: {matched_country.get('vaping_e_cigarette_legality')}
- Primary transport: {matched_country.get('primary_ride_hailing_apps')}
- Tap Water Safety: {'Potable (Safe)' if matched_country.get('tap_water_potable') else 'Not Potable - Drink Bottled Water'}

Retrieved Regulatory & Compliance Context (RAG):
{rag_context_str}

Shortest Flight Connection Route (Price: INR {flight_res['total_price']:,}):
{flight_details_str}

Please generate the itinerary. Make sure to render this photo tag at the very top:
![{request.destination}]({photo_url})
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Call Groq LLM
        response = generator.llm.invoke(messages)
        itinerary_md = response.content
        
        latency = time.time() - start_time
        REQUEST_COUNT.labels(endpoint="/plan", status_code="200").inc()
        
        return {
            "origin": request.origin,
            "destination": request.destination,
            "profile": request.profile,
            "days": request.days,
            "flight_route": flight_res,
            "itinerary": itinerary_md,
            "photo_url": photo_url,
            "latency": round(latency, 3),
            "sources": rag_results
        }
        
    except HTTPException as he:
        REQUEST_COUNT.labels(endpoint="/plan", status_code=str(he.status_code)).inc()
        raise he
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/plan", status_code="500").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/countries")
def get_countries():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "..", "data", "processed", "travel_data.json")
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
