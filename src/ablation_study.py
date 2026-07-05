import os
import json
import time
import numpy as np
from generator import Generator

# We can import matplotlib to plot, but to ensure it runs headless in Docker without GUI errors,
# we will save the raw data and print a beautiful text-based ASCII chart and save a Markdown table.
# If matplotlib is installed, we can also generate a chart image.

class AblationStudy:
    def __init__(self):
        print("Initializing Ablation Study Experiment...")
        self.generator = Generator()
        
    def load_evaluation_dataset(self) -> list:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        # Try synthetic dataset first, fall back to evaluator static dataset if not found
        synth_path = os.path.join(BASE_DIR, "..", "data", "processed", "synthetic_eval_dataset.json")
        
        if os.path.exists(synth_path):
            print(f"Loading synthetic dataset from {synth_path}")
            with open(synth_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print("Synthetic dataset not found. Falling back to static test queries.")
            from evaluator import EVALUATION_DATASET
            return EVALUATION_DATASET

    def evaluate_precision(self, queries: list, mode: str) -> dict:
        """
        Runs retrieval using different ablation modes and returns average precision.
        Modes: 'dense', 'sparse', 'hybrid', 'hybrid_rerank'
        """
        print(f"\n🧪 Running evaluation in mode: '{mode.upper()}'")
        latencies = []
        precision_scores = []
        
        for item in queries:
            query = item["query"]
            expected_country = item.get("expected_country") or item.get("country")
            
            start_time = time.time()
            
            # Custom retrieval based on mode
            if mode == 'dense':
                results = self.generator.retriever.dense_search(query, top_k=3)
                retrieved_countries = [r["chunk"]["country"] for r in results]
            elif mode == 'sparse':
                results = self.generator.retriever.sparse_search(query, top_k=3)
                retrieved_countries = [r["chunk"]["country"] for r in results]
            elif mode == 'hybrid':
                # Call query without reranker (just RRF)
                results = self.generator.retriever.query(query, retrieve_k=10, final_k=3)
                # Since query does reranking under the hood, let's bypass reranker for true RRF:
                dense_res = self.generator.retriever.dense_search(query, top_k=10)
                sparse_res = self.generator.retriever.sparse_search(query, top_k=10)
                rrf_scores = {}
                chunk_map = {}
                for rank, r in enumerate(dense_res):
                    cid = r["chunk"]["chunk_id"]
                    chunk_map[cid] = r["chunk"]
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60 + rank + 1))
                for rank, r in enumerate(sparse_res):
                    cid = r["chunk"]["chunk_id"]
                    chunk_map[cid] = r["chunk"]
                    rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (60 + rank + 1))
                sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:3]
                retrieved_countries = [chunk_map[cid]["country"] for cid, _ in sorted_rrf]
            elif mode == 'hybrid_rerank':
                results = self.generator.retriever.query(query, retrieve_k=10, final_k=3)
                retrieved_countries = [r["country"] for r in results]
                
            latency = time.time() - start_time
            latencies.append(latency)
            
            precision = 1.0 if expected_country in retrieved_countries else 0.0
            precision_scores.append(precision)
            
        return {
            "mode": mode,
            "avg_precision": float(np.mean(precision_scores)),
            "avg_latency_ms": float(np.mean(latencies) * 1000)
        }

    def run_study(self):
        queries = self.load_evaluation_dataset()
        if not queries:
            print("No queries available for ablation study.")
            return
            
        print(f"Loaded {len(queries)} evaluation cases.")
        
        modes = ['dense', 'sparse', 'hybrid', 'hybrid_rerank']
        report = []
        
        for mode in modes:
            metrics = self.evaluate_precision(queries, mode)
            report.append(metrics)
            time.sleep(1.0)
            
        print("\n" + "=" * 60)
        print("🧪 ABLATION STUDY EXPERIMENTAL RESULTS")
        print("=" * 60)
        
        # Save Markdown Report
        report_content = f"""# RAG Retrieval Ablation Study Report

This study compares the retrieval performance of four different search architectures on the Outbound-India Travel dataset.

## Experimental Metrics
| Search Architecture | Retrieval Precision (Top-3 Match) | Average Latency (ms) | Key Benefit |
| :--- | :--- | :--- | :--- |
| **Dense Only (FAISS)** | `{report[0]['avg_precision']*100:.1f}%` | `{report[0]['avg_latency_ms']:.1f} ms` | Semantic comprehension, handles synonyms. |
| **Sparse Only (BM25)** | `{report[1]['avg_precision']*100:.1f}%` | `{report[1]['avg_latency_ms']:.1f} ms` | Precise keyword matching (fines, visa codes). |
| **Hybrid (FAISS + BM25)** | `{report[2]['avg_precision']*100:.1f}%` | `{report[2]['avg_latency_ms']:.1f} ms` | Fuses semantic & keyword rankings via RRF. |
| **Hybrid + Reranker (MiniLM)** | `{report[3]['avg_precision']*100:.1f}%` | `{report[3]['avg_latency_ms']:.1f} ms` | Uses Cross-Encoder to select optimal context. |

## ASCII Performance Chart
```text
Retrieval Precision:
Dense Only   : [{'#' * int(report[0]['avg_precision']*20)}{' ' * (20 - int(report[0]['avg_precision']*20))}] {report[0]['avg_precision']*100:.1f}%
Sparse Only  : [{'#' * int(report[1]['avg_precision']*20)}{' ' * (20 - int(report[1]['avg_precision']*20))}] {report[1]['avg_precision']*100:.1f}%
Hybrid RRF   : [{'#' * int(report[2]['avg_precision']*20)}{' ' * (20 - int(report[2]['avg_precision']*20))}] {report[2]['avg_precision']*100:.1f}%
Hybrid+Rerank: [{'#' * int(report[3]['avg_precision']*20)}{' ' * (20 - int(report[3]['avg_precision']*20))}] {report[3]['avg_precision']*100:.1f}%
```
"""
        print(report_content)
        
        # Save to markdown file
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(BASE_DIR, "..", "data", "processed", "ablation_study_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"Ablation study report written to {report_path}")
        
        # Also try to generate chart image if matplotlib is installed
        try:
            import matplotlib.pyplot as plt
            labels = ['Dense (FAISS)', 'Sparse (BM25)', 'Hybrid (RRF)', 'Hybrid + Rerank']
            precisions = [r['avg_precision'] * 100 for r in report]
            
            plt.figure(figsize=(8, 5))
            colors = ['#ff6b35', '#f7931e', '#4ade80', '#60a5fa']
            bars = plt.bar(labels, precisions, color=colors, edgecolor='grey', width=0.6)
            plt.ylabel('Retrieval Precision (%)')
            plt.title('RAG Retrieval Performance Ablation Study')
            plt.ylim(0, 105)
            
            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')
                
            chart_path = os.path.join(BASE_DIR, "..", "data", "processed", "ablation_chart.png")
            plt.savefig(chart_path, dpi=300)
            print(f"Ablation performance chart plotted and saved to {chart_path}")
        except Exception as e:
            print("Matplotlib chart generation skipped (runs in headless mode).")

if __name__ == "__main__":
    study = AblationStudy()
    study.run_study()
