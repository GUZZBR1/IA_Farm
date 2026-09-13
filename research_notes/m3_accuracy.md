# 🎯 M3: Accuracy Validation (Chemical Dosage)
## Deterministic Tool-use Strategy
To ensure zero-error in chemical dosage:
1. **Constrained Output:** Use Pydantic/JSON-Schema to force the LLM to only output keys `product` and `dosage_value`.
2. **Execution Layer:** The LLM does NOT calculate the dose. It provides the `base_rate` and `area`. A local Python function performs the multiplication: `Total = base_rate * area`.
3. **Verification:** Cross-reference the result against a "Safety Max" table before displaying to the user.
