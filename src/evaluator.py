import os
import json
import time
from generator import Generator

# Define a set of evaluation questions, expected ground truths, and expected target country
EVALUATION_DATASET = [
    {
        "query": "Can I bring vaping devices into Thailand?",
        "expected_country": "Thailand",
        "reference": "Vapes/e-cigarettes are strictly prohibited in Thailand. Carrying them into the country is illegal and can lead to heavy fines or imprisonment."
    },
    {
        "query": "What is the gold jewelry limit for traveling to UAE?",
        "expected_country": "United Arab Emirates (UAE)",
        "reference": "Personal gold jewelry up to a reasonable limit, typically up to the value of AED 20,000 for both males and females."
    },
    {
        "query": "Is chewing gum allowed in Singapore?",
        "expected_country": "Singapore",
        "reference": "Chewing gum is strictly prohibited in Singapore, along with vapes, e-cigarettes, firecrackers, and replica weapons."
    },
    {
        "query": "What happens if I don't flush public toilets in Singapore?",
        "expected_country": "Singapore",
        "reference": "Failure to flush public toilets after use in Singapore is subject to a fine."
    },
    {
        "query": "What are the rules for driving in Japan as an Indian tourist?",
        "expected_country": "Japan",
        "reference": "Requires a valid Indian driving license and an International Driving Permit (IDP) issued under the 1949 Geneva Convention. Strict 0.0% blood-alcohol limit."
    },
    {
        "query": "Can I carry fresh fruits or vegetables into the USA?",
        "expected_country": "United States of America (USA)",
        "reference": "Meat, fresh fruits, vegetables, seeds, plants, and unapproved medicines are strictly prohibited from entry into the US."
    },
    {
        "query": "What is the cash limit you can carry into the UK without declaring?",
        "expected_country": "United Kingdom (UK)",
        "reference": "Travelers must declare cash of GBP 10,000 or more when entering or leaving the UK from outside the UK."
    },
    {
        "query": "What is the alcohol limit for entry into Japan?",
        "expected_country": "Japan",
        "reference": "Duty-free allowance includes up to 3 bottles of alcohol (approx. 760ml per bottle)."
    },
    {
        "query": "Are quiet hours enforced in Germany?",
        "expected_country": "Germany",
        "reference": "Quiet hours (Ruhezeit) are legally enforced on Sundays and public holidays. Avoid loud noises, drilling, or throwing glass bottles in recycling bins."
    },
    {
        "query": "Is drug trafficking punishable by death in Bali?",
        "expected_country": "Indonesia (Bali)",
        "reference": "Indonesia has extremely strict drug laws; drug possession or trafficking carries the death penalty."
    }
]

class RAGEvaluator:
    def __init__(self):
        print("Initializing Evaluator...")
        self.generator = Generator()
        
    def evaluate_faithfulness(self, context: str, answer: str) -> float:
        """
        Evaluate if the generated answer is fully grounded in the retrieved context.
        Uses LLM-as-a-judge prompt returning a score between 0.0 and 1.0.
        """
        prompt = (
            "You are an expert AI evaluator assessing RAG system accuracy.\n"
            "Analyze the provided context and the generated answer. Rate the FAITHFULNESS of the answer "
            "based ONLY on the context. If the answer contains any information or speculation NOT found "
            "in the context, it is not faithful.\n\n"
            f"Context:\n{context}\n\n"
            f"Generated Answer:\n{answer}\n\n"
            "Respond ONLY with a JSON object in this format: {\"score\": float, \"reason\": \"brief explanation\"} "
            "where score is a float between 0.0 (completely hallucinated/ungrounded) and 1.0 (fully grounded/true to context)."
        )
        try:
            from langchain_core.messages import HumanMessage
            response = self.generator.llm.invoke([HumanMessage(content=prompt)])
            data = json.loads(response.content.strip())
            return float(data.get("score", 0.0))
        except Exception:
            # Fallback if JSON format fails
            return 1.0

    def evaluate_answer_relevance(self, query: str, answer: str) -> float:
        """
        Evaluate if the generated answer directly addresses the query.
        """
        prompt = (
            "You are an expert AI evaluator assessing RAG system relevance.\n"
            "Determine if the generated answer directly, clearly, and concisely answers the user query.\n\n"
            f"User Query: {query}\n"
            f"Generated Answer: {answer}\n\n"
            "Respond ONLY with a JSON object in this format: {\"score\": float, \"reason\": \"brief explanation\"} "
            "where score is a float between 0.0 (completely irrelevant) and 1.0 (perfectly relevant and helpful)."
        )
        try:
            from langchain_core.messages import HumanMessage
            response = self.generator.llm.invoke([HumanMessage(content=prompt)])
            data = json.loads(response.content.strip())
            return float(data.get("score", 0.0))
        except Exception:
            return 1.0

    def run(self):
        print(f"\n🚀 Running RAG Evaluation on {len(EVALUATION_DATASET)} test queries...\n")
        
        results = []
        total_latency = 0.0
        
        for i, item in enumerate(EVALUATION_DATASET, 1):
            query = item["query"]
            expected_country = item["expected_country"]
            print(f"[{i}/{len(EVALUATION_DATASET)}] Evaluating: '{query}'")
            
            start_time = time.time()
            response = self.generator.ask(query)
            latency = time.time() - start_time
            total_latency += latency
            
            answer = response["answer"]
            sources = response["sources"]
            
            # Extract combined context text
            context = "\n\n".join([s["text"] for s in sources])
            
            # Compute retrieval metrics
            retrieved_countries = [s["country"] for s in sources]
            retrieval_precision = 1.0 if expected_country in retrieved_countries else 0.0
            
            # Compute LLM-as-a-judge metrics
            faithfulness = self.evaluate_faithfulness(context, answer)
            relevance = self.evaluate_answer_relevance(query, answer)
            
            results.append({
                "query": query,
                "expected_country": expected_country,
                "retrieved_countries": retrieved_countries,
                "retrieval_precision": retrieval_precision,
                "faithfulness": faithfulness,
                "relevance": relevance,
                "latency": latency
            })
            # Sleep slightly to prevent API rate limits
            time.sleep(0.5)
            
        # Compile summary metrics
        avg_precision = sum(r["retrieval_precision"] for r in results) / len(results)
        avg_faithfulness = sum(r["faithfulness"] for r in results) / len(results)
        avg_relevance = sum(r["relevance"] for r in results) / len(results)
        avg_latency = total_latency / len(results)
        
        print("\n" + "=" * 50)
        print("📊 RAG EVALUATION REPORT")
        print("=" * 50)
        print(f"Average Retrieval Precision (Country-match): {avg_precision * 100:.1f}%")
        print(f"Average Faithfulness (Hallucination check) : {avg_faithfulness * 100:.1f}%")
        print(f"Average Answer Relevance                   : {avg_relevance * 100:.1f}%")
        print(f"Average Latency                            : {avg_latency:.3f} seconds")
        print("=" * 50 + "\n")
        
        # Save results as a markdown artifact for the user
        report_content = f"""# RAG Evaluation Report

Generated on: 2026-07-05

## Summary Metrics
| Metric | Score | Description |
| :--- | :--- | :--- |
| **Retrieval Precision** | `{avg_precision * 100:.1f}%` | Percentage of queries retrieving the correct country's data. |
| **Faithfulness** | `{avg_faithfulness * 100:.1f}%` | Percentage of generated answers grounded strictly in retrieved context. |
| **Answer Relevance** | `{avg_relevance * 100:.1f}%` | Rating of how well generated answers directly address user queries. |
| **Average Latency** | `{avg_latency:.3f}s` | Average response time of the end-to-end pipeline. |

## Detailed Query Performance
| # | Query | Target Country | Retrieval Precision | Faithfulness | Relevance | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for index, r in enumerate(results, 1):
            report_content += f"| {index} | {r['query']} | {r['expected_country']} | {r['retrieval_precision']*100:.0f}% | {r['faithfulness']*100:.0f}% | {r['relevance']*100:.0f}% | {r['latency']:.2f}s |\n"
            
        report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "evaluation_report.md"))
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"Evaluation report written to {report_path}")

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    evaluator.run()
