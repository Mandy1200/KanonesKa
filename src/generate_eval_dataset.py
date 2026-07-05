import os
import json
import random
import time
from generator import Generator
from langchain_core.messages import HumanMessage

class SyntheticDatasetGenerator:
    def __init__(self):
        print("Initializing Synthetic Dataset Generator...")
        self.generator = Generator()
        
    def generate_triplets(self, num_questions: int = 50, output_path: str = None):
        """
        Reads travel_data.json, randomly samples country profiles, and uses ChatGroq
        to generate realistic Question-Context-Ground Truth triplets.
        """
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(BASE_DIR, "..", "data", "processed", "travel_data.json")
        
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Travel data database not found: {data_path}")
            
        with open(data_path, "r", encoding="utf-8") as f:
            countries_data = json.load(f)
            
        print(f"Loaded {len(countries_data)} countries. Starting synthetic generation...")
        
        dataset = []
        categories_to_query = [
            ("visa_requirements", "Visa Requirements"),
            ("customs_duty_free_limits", "Customs & Duty-Free Limits"),
            ("tipping_culture_rules", "Tipping & Shopping"),
            ("primary_ride_hailing_apps", "Local Transportation"),
            ("scam_alerts_common", "Emergency & Safety"),
            ("vaping_e_cigarette_legality", "Cultural Taboos & Laws"),
            ("alcohol_availability_laws", "Food & Alcohol Regulations")
        ]
        
        generated_count = 0
        attempts = 0
        max_attempts = num_questions * 2
        
        while generated_count < num_questions and attempts < max_attempts:
            attempts += 1
            
            # Select random country and random category
            country_profile = random.choice(countries_data)
            country = country_profile["country"]
            category_key, category_name = random.choice(categories_to_query)
            
            content = country_profile.get(category_key, "")
            if not content or len(str(content)) < 15:
                continue
                
            context = f"[{country} - {category_name}]: {content}"
            
            # Formulate the prompt for Groq LLM to generate a question & answer
            prompt = (
                "You are a dataset generator assistant. Your task is to write a realistic, natural user query "
                "and its corresponding ground-truth answer based ONLY on the provided context block.\n\n"
                f"Context Block:\n{context}\n\n"
                "INSTRUCTIONS:\n"
                "1. The query must be something an Indian tourist would naturally ask (e.g. 'Can I carry gold to UAE?' or 'What cab app should I download in France?').\n"
                "2. The ground-truth answer must be completely factual, concise, and fully supported by the context.\n"
                "3. Respond ONLY with a valid JSON object in this format:\n"
                "{\n"
                "  \"query\": \"the generated question string\",\n"
                "  \"ground_truth\": \"the generated answer string\"\n"
                "}"
            )
            
            try:
                response = self.generator.llm.invoke([HumanMessage(content=prompt)])
                triplet = json.loads(response.content.strip())
                
                # Verify structure
                if "query" in triplet and "ground_truth" in triplet:
                    dataset.append({
                        "id": generated_count + 1,
                        "country": country,
                        "category": category_key,
                        "context": context,
                        "query": triplet["query"],
                        "ground_truth": triplet["ground_truth"]
                    })
                    generated_count += 1
                    print(f"Generated ({generated_count}/{num_questions}): {triplet['query']}")
                    
                time.sleep(0.5)  # Avoid rate limits
            except Exception as e:
                print(f"Error generating triplet: {e}")
                time.sleep(1.0)
                
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, indent=4, ensure_ascii=False)
            print(f"\nSuccessfully generated {len(dataset)} triplets and saved to {output_path}")
            
        return dataset

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "..", "data", "processed", "synthetic_eval_dataset.json")
    
    generator = SyntheticDatasetGenerator()
    generator.generate_triplets(num_questions=50, output_path=output_path)
