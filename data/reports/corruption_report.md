# Data Corruption & Self-Healing Comparison Report

## 1. 3-State Performance Comparison Matrix

| Metric / Signal | Baseline | Corrupted | Repaired | Change (Corruption) | Recovery |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Retrieval Hit Rate** | 1.0000 | 0.5000 | 1.0000 | -0.5000 | +0.5000 |
| **Mean Token F1** | 1.0000 | 0.8506 | 1.0000 | -0.1494 | +0.1494 |
| **Judge Accuracy** | 1.0000 | 0.9000 | 1.0000 | -0.1000 | +0.1000 |
| **Data Quality Status** | PASSED | FAILED | PASSED | Impacted | Recovered |
| **Freshness SLA Status** | FRESH | STALE | FRESH | Impacted | Recovered |

## 2. Causal Analysis & Findings
1. **Silent Failure Impact:** Data corruption causes significant performance degradation in Retrieval Hit Rate and Token F1, triggering Data Quality & Freshness alerts.
2. **Self-Healing Recovery:** Idempotent Repair from raw snapshots restores Data Quality validation and returns RAG Agent evaluation metrics back to Baseline performance.
