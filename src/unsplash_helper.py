import os
import requests
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=800&auto=format&fit=crop"

def get_city_photo(query_str: str) -> str:
    """
    Fetches a high-quality landscape photo URL for a given destination city using the Unsplash API.
    Gracefully falls back to a travel landscape photo if limits are reached or on network failures.
    """
    if not UNSPLASH_ACCESS_KEY:
        print("⚠️ Unsplash API Access Key missing. Using fallback travel image.")
        return FALLBACK_IMAGE
        
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": f"{query_str} landscape",
            "client_id": UNSPLASH_ACCESS_KEY,
            "per_page": 1,
            "orientation": "landscape"
        }
        res = requests.get(url, params=params, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data.get("results"):
                # Return the regular size image url
                photo_url = data["results"][0]["urls"]["regular"]
                # Append constraints for clean rendering
                return f"{photo_url}&w=800&auto=format&fit=crop"
        print(f"⚠️ Unsplash search returned status {res.status_code}. Using fallback.")
    except Exception as e:
        print(f"⚠️ Unsplash request failed: {e}. Using fallback.")
        
    return FALLBACK_IMAGE

if __name__ == "__main__":
    test_city = "Bali"
    img = get_city_photo(test_city)
    print(f"Test image for {test_city}: {img}")
