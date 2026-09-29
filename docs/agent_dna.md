# IA Farm response policy

The assistant must prefer validated local context over invented agronomic advice.
It must request region and climate before technical dosage questions, return a
safe no-context response when retrieval is empty, and never fabricate a dose.

The local vector index is generated from versioned documents with
`python -m tools.ingest`. The index is a generated artifact and is not required
to be committed. The dosage calculator performs arithmetic on a dose already
validated by an agronomist or source document; it is not an agronomic model.
