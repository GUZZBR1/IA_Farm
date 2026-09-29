# Golden Set policy

The checked-in Golden Set validates safety and retrieval contracts, not agronomic
truth. It must not contain invented product doses presented as authoritative.

The deterministic persona simulation contains ten progressive batteries, each
run by three scripted user agents. Cases cover:

- requesting region and climate before a technical dosage response;
- failing closed when retrieval returns no validated context;
- preserving session region/climate and passing retrieved fixture context;
- preventing ungrounded dose units in safe fallback responses.

Agronomic acceptance cases may be added only with a source citation, crop and
region metadata, review date, and approval from a qualified agronomist. Until
then, `tests/run_golden_set.py` is a deterministic orchestration simulation and
not a field-certification report. A green result is not a measurement of live
LLM safety or Android hardware behavior.

Run it with:

```bash
python tests/run_golden_set.py
```
