
import sys
import os
sys.path.append("/tmp/ia_farm_libs")

try:
    import faiss
    import sentence_transformers
    print("SUCCESS: Libraries loaded from /tmp/ia_farm_libs")
except ImportError as e:
    print(f"FAILURE: {e}")
