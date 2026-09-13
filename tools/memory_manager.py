import mmap
import os
import hashlib
import json
from typing import Any, Optional

class MemoryManager:
    """
    MemoryManager provides RAM optimization techniques for mobile deployment,
    specifically using memory-mapped files (mmap) for large data and 
    local context caching for frequent queries.
    """

    def __init__(self, cache_file: str = "context_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_cache(self):
        """Persists the current cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f)
        except IOError as e:
            print(f"Error saving cache: {e}")

    def mmap_load(self, file_path: str):
        """
        Opens a file using mmap. This allows the OS to map the file into 
        virtual memory, loading pages only when accessed.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_obj = open(file_path, "rb")
        # mmap.mmap(fileno, length, access=mmap.ACCESS_READ)
        return mmap.mmap(file_obj.fileno(), 0, access=mmap.ACCESS_READ), file_obj

    def get_cached_context(self, query: str) -> Optional[Any]:
        """
        Retrieves context from cache using a hash of the query.
        """
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        return self.cache.get(query_hash)

    def set_cached_context(self, query: str, context: Any):
        """
        Stores the retrieved context in the cache for a given query.
        """
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        self.cache[query_hash] = context
        # We don't auto-save every time to avoid disk I/O overhead; 
        # call save_cache() periodically.
