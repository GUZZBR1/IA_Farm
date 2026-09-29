# Golden Set policy

The checked-in Golden Set validates safety and retrieval contracts, not agronomic
truth. It must not contain invented product doses presented as authoritative.

Current cases cover:

- requesting region and climate before a technical dosage response;
- failing closed when retrieval returns no validated context;
- allowing a response only when the retriever supplies context;
- preventing ungrounded dose units in safe fallback responses.

Agronomic acceptance cases may be added only with a source citation, crop and
region metadata, review date, and approval from a qualified agronomist. Until
then, `tests/run_golden_set.py` is a guardrail suite and not a field-certification
report.

Run it with:

```bash
python tests/run_golden_set.py
```
