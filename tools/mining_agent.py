
import time
import requests
from tools.vector_engine import VectorEngine
from tools.memory_manager import MemoryManager

# Config
API_KEY = "YOUR_OPENROUTER_KEY" # To be replaced by env var
CORN_TOPICS = [
    "adubação de nitrogênio milho embrapa",
    "controle de lagarta do cartucho milho",
    "manejo de irrigação milho sudeste",
    "dosagem de fósforo e potássio milho",
    "combate a ferrugem asiática milho"
]

def mine_knowledge():
    print("Starting Mining Process...")
    ve = VectorEngine(api_key=API_KEY)
    
    # Simulating the a la Chrome search and extraction
    for topic in CORN_TOPICS:
        print(f"Mining topic: {topic}")
        # In a real flow, this would involve a search API or Chrome scraping
        # For now, we simulate the found technical data to build the base
        mock_data = [
            {"text": f"Para {topic}, a recomendação técnica é a aplicação de dose X kg/ha conforme manual Embrapa.", 
             "metadata": {"source": "Embrapa", "topic": topic, "category": "technical"}}
        ]
        ve.add_documents(mock_data)
        time.sleep(1) # Avoid rate limits

    print("Mining cycle complete. Knowledge persisted to disk.")

if __name__ == "__main__":
    mine_knowledge()
