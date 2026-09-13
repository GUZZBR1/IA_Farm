
import sys
sys.path.append('/home/guzzbr/meus-projetos/IA_Farm')
try:
    from sentence_transformers import SentenceTransformer
    print("Starting download of the embedding model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("SUCCESS: Model downloaded and loaded into RAM!")
except Exception as e:
    print(f"DOWNLOAD_ERROR: {e}")
