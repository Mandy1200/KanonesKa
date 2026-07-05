import os
import json

def chunk_travel_data(input_path: str) -> list:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    chunks = []
    chunk_id = 1
    
    for c in data:
        country = c["country"]
        
        # Category 1: Connectivity & Tech Logistics
        tech_text = (
            f"[{country} - Connectivity & Tech Logistics]: "
            f"SIM card availability at airports is {c['sim_card_availability']}. "
            f"Major telecom providers for tourists are {c['major_telecom_providers']}. "
            f"Electrical outlets use {c['power_plug_types']} plugs, operating at {c['voltage_frequency']}. "
            f"Average public/hotel WiFi speed is {c['average_wifi_speed_mbps']} Mbps."
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'tech_logistics', 'text': tech_text})
        chunk_id += 1
        
        # Category 2: Financial, Tipping, & Shopping Mechanics
        finance_text = (
            f"[{country} - Finance & Shopping]: "
            f"The local currency code is {c['local_currency_code']}. "
            f"Payment reliance is {c['cash_vs_card_reliance']}. "
            f"Preferred digital wallets are {c['preferred_digital_wallets']}. "
            f"Tipping culture rule: {c['tipping_culture_rules']} "
            f"Tax-free shopping is {'available' if c['tax_free_shopping_available'] else 'not available'}. "
            f"Minimum spend for tax refund is {c['local_currency_code']} {c['min_spend_tax_refund']}."
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'finance_shopping', 'text': finance_text})
        chunk_id += 1
        
        # Category 3: Local Transportation & Navigation
        transit_text = (
            f"[{country} - Transportation & Navigation]: "
            f"Primary ride-hailing apps are {c['primary_ride_hailing_apps']}. "
            f"Metro/train transit is {'available' if c['metro_train_availability'] else 'not available'}. "
            f"Tourist transit card name: {c['tourist_transit_pass_name']}. "
            f"Jaywalking laws are {'strictly enforced' if c['jaywalking_laws_enforced'] else 'not strictly enforced'}."
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'transportation', 'text': transit_text})
        chunk_id += 1
        
        # Category 4: Emergency, Safety, & Health Risks
        safety_text = (
            f"[{country} - Emergency & Safety]: "
            f"Emergency police number is {c['emergency_police_number']}. "
            f"Emergency medical/ambulance number is {c['emergency_medical_number']}. "
            f"Tap water is {'potable (safe to drink)' if c['tap_water_potable'] else 'not potable (avoid drinking)'}. "
            f"Common tourist scams to avoid: {c['scam_alerts_common']} "
            f"Solo female safety rating is {c['solo_female_safety_rating']}. "
            f"Indian Embassy contact details: {c['emergency_indian_embassy_contact']}"
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'safety_emergency', 'text': safety_text})
        chunk_id += 1
        
        # Category 5: Cultural Taboos, Etiquette, & Penalties
        etiquette_text = (
            f"[{country} - Cultural Taboos & Laws]: "
            f"Dress code restrictions: {c['dress_code_restrictions']} "
            f"LGBTQ safety & legal status: {c['lgbtq_safety_legal_status']}. "
            f"Public Display of Affection (PDA) is {c['public_display_of_affection_rules']}. "
            f"Photography and drone restrictions: {c['photography_restrictions']} "
            f"Vaping and e-cigarette legality: {c['vaping_e_cigarette_legality']}."
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'etiquette_laws', 'text': etiquette_text})
        chunk_id += 1
        
        # Category 6: Seasonal, Timing, & Crowding Dynamics
        seasonal_text = (
            f"[{country} - Seasons & Tourism Dynamics]: "
            f"Peak tourism months are {c['peak_tourism_months']}. "
            f"Shoulder seasons (best value) are {c['shoulder_season_months']}. "
            f"Avoid monsoons/cyclones in {c['monsoon_cyclone_months']}. "
            f"Major national closures and holiday impacts: {c['major_national_closures']}"
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'seasonal_timing', 'text': seasonal_text})
        chunk_id += 1
        
        # Category 7: Food, Lifestyle, & Language
        food_text = (
            f"[{country} - Food & Language]: "
            f"Primary languages spoken are {c['primary_languages_spoken']}. "
            f"English proficiency level is {c['english_proficiency_level']}. "
            f"Vegetarian and vegan friendliness is {c['vegetarian_vegan_friendliness']}. "
            f"Halal food availability is {c['halal_food_availability']}. "
            f"Alcohol laws and availability: {c['alcohol_availability_laws']}"
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'food_language', 'text': food_text})
        chunk_id += 1
        
        # Category 8: Search Metadata & Links
        meta_text = (
            f"[{country} - Verification Links & Tags]: "
            f"Search keywords: {', '.join(c['search_keywords_tags'])}. "
            f"Official government travel link for visa/entry check: {c['official_government_travel_link']}."
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'metadata_links', 'text': meta_text})
        chunk_id += 1
        
        # Category 9: Visa Requirements
        visa_text = (
            f"[{country} - Visa Requirements]: {c['visa_requirements']}"
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'visa_requirements', 'text': visa_text})
        chunk_id += 1
        
        # Category 10: Customs & Duty-Free Limits
        customs_text = (
            f"[{country} - Customs & Duty-Free Limits]: {c['customs_duty_free_limits']}"
        )
        chunks.append({'chunk_id': chunk_id, 'country': country, 'category': 'customs_limits', 'text': customs_text})
        chunk_id += 1
        
    return chunks

def save_chunks(chunks: list, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(chunks, file, indent=4, ensure_ascii=False)
    print(f"Chunks saved successfully ({len(chunks)} chunks) to {output_path}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(BASE_DIR, "..", "data", "processed", "travel_data.json")
    output_file = os.path.join(BASE_DIR, "..", "data", "processed", "travel_chunks.json")

    try:
        chunks = chunk_travel_data(input_file)
        save_chunks(chunks, output_file)
    except Exception as e:
        print(f"Error: {e}")