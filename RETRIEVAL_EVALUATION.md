# Retrieval evaluation

## Evaluation sets

`tests/retrieval_eval_dataset.json` is a synthetic mechanics dataset with stable queries and fixture records. Its scores are `SYNTHETIC_RETRIEVAL_EVALUATION`; they are not agronomic accuracy, field performance, or evidence that corn queries are supported. The Agronomic Golden Set remains separate and contains zero approved cases.

## Current run

Run the lexical baseline with:

```sh
python -m tools.retrieval_evaluation --suite synthetic --backend lexical
```

BM25 runs on the synthetic fixture set only. Vector evaluation requires installed NumPy/FAISS/Sentence-Transformers, a local model directory, and a model manifest with an immutable revision and verified artifact hash:

```sh
python -m tools.retrieval_evaluation --suite synthetic --backend vector \
  --model /path/to/local/model --model-manifest /path/to/model-manifest.json
```

Current vector status: `BLOCKED_BY_ENVIRONMENT` (`DEPENDENCY_MISSING`); no vector score is reported. Hybrid is not implemented or compared because vector baseline could not run.

Latest BM25 result on WSL/Linux: 5 synthetic cases over 3 synthetic records; Recall@3 1.000, Precision@3 0.667, MRR@3 1.000, abstention accuracy 1.000, no-result accuracy 1.000, wrong-region rate 0.000, forbidden-source rate 0.000, mean latency 0.155 ms. These small fixture results demonstrate only lexical mechanics and are not a ranking-quality or agronomic claim.

## Metrics and interpretation

The runner records recall/precision at K, MRR, no-result accuracy, wrong-region and forbidden-source rates, filter mismatch, latency, dataset/corpus hashes, configuration, Python, and platform when applicable. Metrics with no grounded labels remain null. Synthetic score values measure string retrieval mechanics only. Agronomic claims require approved evidence-backed query labels and remain unavailable until human review.

Metadata filtering regression remains covered: vector top-K expands beyond the original `k * 10` candidate window before giving up. No empirical comparison of post-search expansion against prefiltered indexes has been measured. No semantic threshold is selected. No reranker is enabled.

## Next experiment gate

Create a complete isolated target-platform lock and local model manifest, run the actual vector suite with downloads disabled, save the environment diagnostic and JSON report, then compare against BM25 on the same synthetic cases. Only after sources are approved and queries carry qualified record labels may an agronomic retrieval comparison be scored.
