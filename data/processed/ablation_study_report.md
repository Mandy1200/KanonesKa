# RAG Retrieval Ablation Study Report

This study compares the retrieval performance of four different search architectures on the Outbound-India Travel dataset.

## Experimental Metrics
| Search Architecture | Retrieval Precision (Top-3 Match) | Average Latency (ms) | Key Benefit |
| :--- | :--- | :--- | :--- |
| **Dense Only (FAISS)** | `100.0%` | `15.7 ms` | Semantic comprehension, handles synonyms. |
| **Sparse Only (BM25)** | `28.0%` | `0.8 ms` | Precise keyword matching (fines, visa codes). |
| **Hybrid (FAISS + BM25)** | `96.0%` | `63.9 ms` | Fuses semantic & keyword rankings via RRF. |
| **Hybrid + Reranker (MiniLM)** | `98.0%` | `34.6 ms` | Uses Cross-Encoder to select optimal context. |

## ASCII Performance Chart
```text
Retrieval Precision:
Dense Only   : [####################] 100.0%
Sparse Only  : [#####               ] 28.0%
Hybrid RRF   : [################### ] 96.0%
Hybrid+Rerank: [################### ] 98.0%
```
