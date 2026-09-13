# 🔄 M4: Offline Delta Updates
## Knowledge Versioning Strategy
- **Vector DB:** Use HNSW (Hierarchical Navigable Small World) for local storage.
- **Delta Mechanism:** 
    - Instead of replacing the whole index, implement "Segmented Indices".
    - New knowledge is added to a new small segment file.
    - Search queries across all segments and merge results.
- **Versioning:** Use a Manifest file (JSON) containing hashes of the current segments.
