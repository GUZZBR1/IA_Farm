
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
try:
    from sentence_transformers import SentenceTransformer
    print("Starting download of the embedding model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("SUCCESS: Model downloaded and loaded into RAM!")
except Exception as e:
    print(f"DOWNLOAD_ERROR: {e}")
