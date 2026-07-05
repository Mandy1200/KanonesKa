import heapq

# City to IATA Airport Code mapping (incorporating India's top 100 cities)
CITY_TO_CODE = {
    # 5 Major Hubs
    "bhubaneswar": "BBI",
    "delhi": "DEL",
    "mumbai": "BOM",
    "kolkata": "CCU",
    "bangalore": "BLR",
    
    # North India
    "new delhi": "DEL",
    "noida": "DEL",
    "gurgaon": "DEL",
    "ghaziabad": "DEL",
    "faridabad": "DEL",
    "jaipur": "JAI",
    "jodhpur": "JDH",
    "udaipur": "UDR",
    "kota": "DEL",
    "lucknow": "LKO",
    "kanpur": "KNU",
    "agra": "AGR",
    "varanasi": "VNS",
    "prayagraj": "IXD",
    "amritsar": "ATQ",
    "ludhiana": "LDH",
    "jalandhar": "DEL",
    "srinagar": "SXR",
    "jammu": "IXJ",
    "dehradun": "DED",
    "chandigarh": "IXC",
    "shimla": "SLV",
    "gorakhpur": "GOP",
    "bareilly": "BEK",
    "aligarh": "DEL",
    "meerut": "DEL",
    "gwalior": "GWL",
    "jhansi": "DEL",
    "haridwar": "DED",
    "rishikesh": "DED",
    "loni": "DEL",
    "firozabad": "AGR",
    "moradabad": "DEL",
    "saharanpur": "DEL",
    
    # West India
    "pune": "PNQ",
    "nagpur": "NAG",
    "nashik": "ISK",
    "aurangabad": "IXU",
    "solapur": "SSE",
    "kolhapur": "KLH",
    "ahmedabad": "AMD",
    "surat": "STV",
    "vadodara": "BDQ",
    "rajkot": "RAJ",
    "indore": "IDR",
    "bhopal": "BHO",
    "jabalpur": "JLR",
    "goa": "GOI",
    "panaji": "GOI",
    "ujjain": "IDR",
    "thane": "BOM",
    "navi mumbai": "BOM",
    "amravati": "NAG",
    "akola": "NAG",
    "kalyan": "BOM",
    "dombivli": "BOM",
    "vasai": "BOM",
    "virar": "BOM",
    "bhavnagar": "BHU",
    "jamnagar": "JGA",
    "junagadh": "RAJ",
    "gandhinagar": "AMD",
    
    # South India
    "chennai": "MAA",
    "hyderabad": "HYD",
    "visakhapatnam": "VTZ",
    "vijayawada": "VGA",
    "guntur": "VGA",
    "nellore": "MAA",
    "tirupati": "TIR",
    "kochi": "COK",
    "trivandrum": "TRV",
    "thiruvananthapuram": "TRV",
    "calicut": "CCJ",
    "kozhikode": "CCJ",
    "coimbatore": "CJB",
    "madurai": "IXM",
    "trichy": "TRZ",
    "salem": "SXV",
    "tiruppur": "CJB",
    "mysore": "MYQ",
    "hubli": "HBX",
    "mangalore": "IXE",
    "belgaum": "IXG",
    "vellore": "MAA",
    "erode": "SXV",
    "kurnool": "HYD",
    "warangal": "HYD",
    "nizamabad": "HYD",
    "karimnagar": "HYD",
    "rajahmundry": "RJA",
    "kakinada": "RJA",
    "davanagere": "BLR",
    "bellary": "VDY",
    "gulbarga": "GBR",
    
    # East India & Central
    "patna": "PAT",
    "gaya": "GAY",
    "ranchi": "IXR",
    "jamshedpur": "IXW",
    "dhanbad": "IXR",
    "raipur": "RPR",
    "bilaspur": "PND",
    "bhilai": "RPR",
    "cuttack": "BBI",
    "rourkela": "RRK",
    "sambalpur": "BBI",
    "puri": "BBI",
    "guwahati": "GAU",
    "shillong": "SHL",
    "imphal": "IMF",
    "agartala": "IXA",
    "gangtok": "GAU",
    "bokaro": "IXR",
    "howrah": "CCU",
    "asansol": "CCU",
    "durgapur": "RDP",
    "siliguri": "IXB",
    "aizawl": "AJL",
    "itanagar": "HGI",
    "kohima": "IMF",
    
    # International Hubs & Destinations
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "singapore": "SIN",
    "kuala lumpur": "KUL",
    "bangkok": "BKK",
    "phuket": "HKT",
    "bali": "DPS",
    "sydney": "SYD",
    "melbourne": "MEL",
    "canberra": "CBR",
    "london": "LHR",
    "manchester": "MAN",
    "tokyo": "HND",
    "osaka": "KIX",
    "paris": "CDG",
    "new york": "JFK",
    "los angeles": "LAX",
    "san francisco": "SFO",
    "toronto": "YYZ",
    "vancouver": "YVR",
    "riyadh": "RUH",
    "jeddah": "JED",
    "doha": "DOH"
}

CODE_TO_CITY = {v: k.title() for k, v in CITY_TO_CODE.items()}

# Mapping of local airports to their nearest major Indian gateway hub
LOCAL_TO_HUB = {
    # West Hub: BOM (Mumbai)
    "PNQ": "BOM",  # Pune
    "NAG": "BOM",  # Nagpur
    "ISK": "BOM",  # Nashik
    "IXU": "BOM",  # Aurangabad
    "SSE": "BOM",  # Solapur
    "KLH": "BOM",  # Kolhapur
    "AMD": "BOM",  # Ahmedabad
    "STV": "BOM",  # Surat
    "BDQ": "BOM",  # Vadodara
    "RAJ": "BOM",  # Rajkot
    "IDR": "BOM",  # Indore
    "BHO": "BOM",  # Bhopal
    "JLR": "BOM",  # Jabalpur
    "GOI": "BOM",  # Goa
    "BHU": "BOM",  # Bhavnagar
    "JGA": "BOM",  # Jamnagar
    
    # North Hub: DEL (Delhi)
    "JAI": "DEL",  # Jaipur
    "JDH": "DEL",  # Jodhpur
    "UDR": "DEL",  # Udaipur
    "LKO": "DEL",  # Lucknow
    "KNU": "DEL",  # Kanpur
    "AGR": "DEL",  # Agra
    "VNS": "DEL",  # Varanasi
    "IXD": "DEL",  # Prayagraj
    "ATQ": "DEL",  # Amritsar
    "LDH": "DEL",  # Ludhiana
    "SXR": "DEL",  # Srinagar
    "IXJ": "DEL",  # Jammu
    "DED": "DEL",  # Dehradun
    "IXC": "DEL",  # Chandigarh
    "SLV": "DEL",  # Shimla
    "GOP": "DEL",  # Gorakhpur
    "BEK": "DEL",  # Bareilly
    "GWL": "DEL",  # Gwalior
    
    # South Hub: BLR (Bangalore)
    "MAA": "BLR",  # Chennai
    "HYD": "BLR",  # Hyderabad
    "VTZ": "BLR",  # Visakhapatnam
    "VGA": "BLR",  # Vijayawada
    "TIR": "BLR",  # Tirupati
    "COK": "BLR",  # Kochi
    "TRV": "BLR",  # Thiruvananthapuram
    "CCJ": "BLR",  # Kozhikode
    "CJB": "BLR",  # Coimbatore
    "IXM": "BLR",  # Madurai
    "TRZ": "BLR",  # Trichy
    "SXV": "BLR",  # Salem
    "MYQ": "BLR",  # Mysore
    "HBX": "BLR",  # Hubli
    "IXE": "BLR",  # Mangalore
    "IXG": "BLR",  # Belgaum
    "VDY": "BLR",  # Bellary
    "GBR": "BLR",  # Gulbarga
    
    # East Hub: CCU (Kolkata)
    "PAT": "CCU",  # Patna
    "GAY": "CCU",  # Gaya
    "IXR": "CCU",  # Ranchi
    "IXW": "CCU",  # Jamshedpur
    "RPR": "CCU",  # Raipur
    "PND": "CCU",  # Bilaspur
    "RRK": "CCU",  # Rourkela
    "GAU": "CCU",  # Guwahati
    "SHL": "CCU",  # Shillong
    "IMF": "CCU",  # Imphal
    "IXA": "CCU",  # Agartala
    "RDP": "CCU",  # Durgapur
    "IXB": "CCU",  # Siliguri
    "AJL": "CCU",  # Aizawl
    "HGI": "CCU"   # Itanagar
}

# Flight connections graph: origin_code -> list of dicts of outgoing flights
FLIGHT_SCHEDULES = {
    # BBI (Bhubaneswar) departures (Domestic legs)
    "BBI": [
        {"to": "CCU", "airline": "IndiGo", "flight_no": "6E-7204", "dep": "08:15", "arr": "09:20", "price": 3500, "duration": "1h 05m"},
        {"to": "DEL", "airline": "Air India", "flight_no": "AI-878", "dep": "13:20", "arr": "15:40", "price": 5800, "duration": "2h 20m"},
        {"to": "BOM", "airline": "Vistara", "flight_no": "UK-785", "dep": "10:10", "arr": "12:35", "price": 6200, "duration": "2h 25m"},
        {"to": "BLR", "airline": "Akasa Air", "flight_no": "QP-1304", "dep": "18:40", "arr": "20:30", "price": 4500, "duration": "1h 50m"}
    ],
    
    # CCU (Kolkata) departures
    "CCU": [
        {"to": "SIN", "airline": "Singapore Airlines", "flight_no": "SQ-517", "dep": "23:50", "arr": "06:40", "price": 14500, "duration": "4h 20m"},
        {"to": "KUL", "airline": "AirAsia", "flight_no": "AK-62", "dep": "12:30", "arr": "19:00", "price": 9800, "duration": "4h 00m"},
        {"to": "BKK", "airline": "Thai Airways", "flight_no": "TG-314", "dep": "02:00", "arr": "06:10", "price": 8500, "duration": "2h 40m"}
    ],
    
    # DEL (Delhi) departures
    "DEL": [
        {"to": "DXB", "airline": "Emirates", "flight_no": "EK-513", "dep": "04:15", "arr": "06:30", "price": 12500, "duration": "3h 45m"},
        {"to": "LHR", "airline": "British Airways", "flight_no": "BA-142", "dep": "02:15", "arr": "07:10", "price": 38000, "duration": "9h 25m"},
        {"to": "HND", "airline": "Japan Airlines", "flight_no": "JL-30", "dep": "19:05", "arr": "06:55", "price": 34000, "duration": "8h 20m"},
        {"to": "SIN", "airline": "IndiGo", "flight_no": "6E-1013", "dep": "21:00", "arr": "05:15", "price": 11000, "duration": "5h 45m"},
        {"to": "KUL", "airline": "Malaysia Airlines", "flight_no": "MH-191", "dep": "23:00", "arr": "07:05", "price": 12000, "duration": "5h 35m"},
        {"to": "RUH", "airline": "Saudia", "flight_no": "SV-761", "dep": "20:00", "arr": "23:15", "price": 16000, "duration": "5h 45m"}
    ],
    
    # BOM (Mumbai) departures
    "BOM": [
        {"to": "DXB", "airline": "FlyDubai", "flight_no": "FZ-402", "dep": "04:55", "arr": "07:00", "price": 11500, "duration": "3h 35m"},
        {"to": "LHR", "airline": "Virgin Atlantic", "flight_no": "VS-355", "dep": "11:15", "arr": "16:40", "price": 36000, "duration": "9h 55m"},
        {"to": "CDG", "airline": "Air France", "flight_no": "AF-217", "dep": "02:10", "arr": "08:15", "price": 39000, "duration": "10h 35m"},
        {"to": "DOH", "airline": "Qatar Airways", "flight_no": "QR-557", "dep": "04:10", "arr": "05:40", "price": 13000, "duration": "4h 00m"},
        {"to": "SIN", "airline": "Singapore Airlines", "flight_no": "SQ-421", "dep": "11:45", "arr": "19:50", "price": 15000, "duration": "5h 35m"},
        {"to": "KUL", "airline": "Malaysia Airlines", "flight_no": "MH-195", "dep": "23:25", "arr": "07:15", "price": 11000, "duration": "5h 20m"},
        {"to": "BKK", "airline": "Thai Airways", "flight_no": "TG-318", "dep": "11:10", "arr": "16:50", "price": 9500, "duration": "4h 10m"}
    ],
    
    # BLR (Bangalore) departures
    "BLR": [
        {"to": "SIN", "airline": "Singapore Airlines", "flight_no": "SQ-511", "dep": "23:10", "arr": "06:10", "price": 13000, "duration": "4h 30m"},
        {"to": "DXB", "airline": "IndiGo", "flight_no": "6E-95", "dep": "18:45", "arr": "21:20", "price": 11000, "duration": "4h 05m"},
        {"to": "BKK", "airline": "Thai AirAsia", "flight_no": "FD-138", "dep": "23:45", "arr": "05:00", "price": 8200, "duration": "3h 45m"}
    ],

    # KUL (Kuala Lumpur) departures
    "KUL": [
        {"to": "DPS", "airline": "AirAsia", "flight_no": "AK-376", "dep": "20:30", "arr": "23:35", "price": 5500, "duration": "3h 05m"},
        {"to": "SYD", "airline": "Malaysia Airlines", "flight_no": "MH-123", "dep": "23:30", "arr": "09:40", "price": 28000, "duration": "8h 10m"}
    ],

    # SIN (Singapore) departures
    "SIN": [
        {"to": "DPS", "airline": "Scoot", "flight_no": "TR-288", "dep": "07:15", "arr": "09:55", "price": 6000, "duration": "2h 40m"},
        {"to": "SYD", "airline": "Singapore Airlines", "flight_no": "SQ-231", "dep": "00:45", "arr": "10:25", "price": 31000, "duration": "7h 40m"}
    ],

    # BKK (Bangkok) departures
    "BKK": [
        {"to": "DPS", "airline": "Thai Lion Air", "flight_no": "SL-258", "dep": "08:00", "arr": "13:20", "price": 6500, "duration": "4h 20m"},
        {"to": "HKT", "airline": "Thai VietJet", "flight_no": "VZ-304", "dep": "10:00", "arr": "11:20", "price": 2200, "duration": "1h 20m"}
    ],

    # DXB (Dubai) departures
    "DXB": [
        {"to": "LHR", "airline": "Emirates", "flight_no": "EK-001", "dep": "07:45", "arr": "12:20", "price": 24000, "duration": "7h 35m"},
        {"to": "RUH", "airline": "Flynas", "flight_no": "XY-202", "dep": "09:30", "arr": "10:45", "price": 5500, "duration": "2h 15m"},
        {"to": "DOH", "airline": "Qatar Airways", "flight_no": "QR-1002", "dep": "11:00", "arr": "11:10", "price": 4800, "duration": "1h 10m"}
    ],

    # DOH (Doha) departures
    "DOH": [
        {"to": "JFK", "airline": "Qatar Airways", "flight_no": "QR-701", "dep": "08:15", "arr": "15:15", "price": 45000, "duration": "14h 00m"},
        {"to": "LHR", "airline": "Qatar Airways", "flight_no": "QR-003", "dep": "07:45", "arr": "13:15", "price": 26000, "duration": "7h 30m"}
    ],

    # LHR (London) departures
    "LHR": [
        {"to": "JFK", "airline": "Virgin Atlantic", "flight_no": "VS-003", "dep": "08:40", "arr": "11:40", "price": 29000, "duration": "8h 00m"},
        {"to": "YYZ", "airline": "Air Canada", "flight_no": "AC-857", "dep": "12:05", "arr": "14:50", "price": 32000, "duration": "7h 45m"}
    ],

    # HND (Tokyo) departures
    "HND": [
        {"to": "LAX", "airline": "ANA", "flight_no": "NH-106", "dep": "22:55", "arr": "16:50", "price": 42000, "duration": "9h 55m"}
    ]
}

def auto_populate_missing_flights():
    origins = ["BBI", "DEL", "BOM", "CCU", "BLR"]
    intl_hubs = ["SIN", "KUL", "BKK", "DXB", "DOH", "LHR", "HND"]
    
    # 1. Connect all local airports to their nearest major hub
    for local, hub in LOCAL_TO_HUB.items():
        if local not in FLIGHT_SCHEDULES:
            FLIGHT_SCHEDULES[local] = []
        # Add a feeder domestic flight segment
        FLIGHT_SCHEDULES[local].append({
            "to": hub,
            "airline": "IndiGo",
            "flight_no": f"6E-{local}{hub}",
            "dep": "06:30",
            "arr": "07:45",
            "price": 3500,
            "duration": "1h 15m"
        })
        
    # 2. Connect major domestic hubs to one another
    for origin in origins:
        if origin not in FLIGHT_SCHEDULES:
            FLIGHT_SCHEDULES[origin] = []
        for gateway in ["DEL", "BOM", "CCU", "BLR"]:
            if origin != gateway:
                if not any(f["to"] == gateway for f in FLIGHT_SCHEDULES[origin]):
                    FLIGHT_SCHEDULES[origin].append({
                        "to": gateway,
                        "airline": "Air India",
                        "flight_no": f"AI-M{origin}{gateway}",
                        "dep": "09:00",
                        "arr": "11:00",
                        "price": 4000,
                        "duration": "2h 00m"
                    })
                    
    # 3. Connect Indian gateway hubs to international transit hubs
    for gateway in ["DEL", "BOM", "CCU", "BLR"]:
        if gateway not in FLIGHT_SCHEDULES:
            FLIGHT_SCHEDULES[gateway] = []
        for hub in intl_hubs:
            if gateway != hub and not any(f["to"] == hub for f in FLIGHT_SCHEDULES[gateway]):
                FLIGHT_SCHEDULES[gateway].append({
                    "to": hub,
                    "airline": "IndiGo",
                    "flight_no": f"6E-H{gateway}{hub}",
                    "dep": "14:00",
                    "arr": "19:30",
                    "price": 12000,
                    "duration": "5h 30m"
                })
                
    # 4. Connect international hubs to all final city destinations
    for hub in intl_hubs:
        if hub not in FLIGHT_SCHEDULES:
            FLIGHT_SCHEDULES[hub] = []
        for city_code in CITY_TO_CODE.values():
            if city_code not in origins and city_code not in intl_hubs and city_code not in LOCAL_TO_HUB:
                if not any(f["to"] == city_code for f in FLIGHT_SCHEDULES[hub]):
                    FLIGHT_SCHEDULES[hub].append({
                        "to": city_code,
                        "airline": "AirAsia" if hub in ["SIN", "KUL", "BKK"] else "Emirates" if hub == "DXB" else "Qatar Airways",
                        "flight_no": f"XX-{hub}{city_code}",
                        "dep": "21:00",
                        "arr": "23:45",
                        "price": 8500,
                        "duration": "2h 45m"
                    })

# Hydrate missing edges to guarantee full reachability across the graph on load
auto_populate_missing_flights()

def resolve_city_to_code(city_input: str) -> str:
    """Translates a user-input city name into its matching IATA Airport Code."""
    clean = city_input.strip().lower()
    for name, code in CITY_TO_CODE.items():
        if name in clean or clean in name:
            return code
    return None

def find_cheapest_flights(origin_city: str, dest_city: str) -> dict:
    """
    Executes Dijkstra's Shortest Path algorithm on the flight schedules
    to calculate the cheapest connection route between two cities.
    """
    origin = resolve_city_to_code(origin_city)
    destination = resolve_city_to_code(dest_city)
    
    if not origin or not destination:
        return {"error": f"Could not resolve airport codes. Origin: '{origin_city}' -> {origin}, Destination: '{dest_city}' -> {destination}"}
        
    # Heap stores: (total_price, count, current_airport, path_list)
    # path_list is a list of flight segments taken
    count = 0
    heap = [(0, count, origin, [])]
    visited = {}
    
    while heap:
        price, _, current, path = heapq.heappop(heap)
        
        # If we reached destination, output the path details
        if current == destination:
            total_duration_minutes = sum(
                (int(s["duration"].split("h")[0]) * 60 + int(s["duration"].split("m")[0].split("h")[-1].strip()))
                for s in path
            )
            h = total_duration_minutes // 60
            m = total_duration_minutes % 60
            
            return {
                "route": [
                    {
                        "from": s["from"],
                        "to": s["to"],
                        "airline": s["airline"],
                        "flight_no": s["flight_no"],
                        "dep": s["dep"],
                        "arr": s["arr"],
                        "price": s["price"],
                        "duration": s["duration"]
                    }
                    for s in path
                ],
                "total_price": price,
                "total_duration": f"{h}h {m}m",
                "layovers": len(path) - 1,
                "origin_code": origin,
                "dest_code": destination
            }
            
        if current in visited and visited[current] <= price:
            continue
        visited[current] = price
        
        # Explore outgoing flights
        flights = FLIGHT_SCHEDULES.get(current, [])
        for f in flights:
            next_hop = f["to"]
            next_price = price + f["price"]
            
            # Record current segment details
            segment = f.copy()
            segment["from"] = current
            
            count += 1
            heapq.heappush(heap, (next_price, count, next_hop, path + [segment]))
            
    return {"error": f"No connecting flight path found between {origin} and {destination}."}

if __name__ == "__main__":
    print("Testing expanded flight router Dijkstra pathfinder...")
    # Pune -> New York (Expected: PNQ -> BOM -> DOH -> JFK)
    res = find_cheapest_flights("Pune", "New York")
    if "error" in res:
        print(f"Error: {res['error']}")
    else:
        print(f"Route Found! Layovers: {res['layovers']} | Price: INR {res['total_price']} | Duration: {res['total_duration']}")
        for step in res["route"]:
            print(f"  {step['from']} ➔ {step['to']} via {step['airline']} ({step['flight_no']}) | Dep: {step['dep']} | Arr: {step['arr']} | {step['duration']}")
