
import sys
import os

# Set path to root for imports
sys.path.append('/home/guzzbr/meus-projetos/IA_Farm')

try:
    from tools.orchastrator import Orchestrator
    from tools.vector_db import LocalVectorDB
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
    sys.exit(1)

# Initialize the REAL components
db = LocalVectorDB()
orch = Orchestrator(vector_db_path='data/vector_index/')

session_state = {}

queries = [
    "Qual a dose de NPK para milho?",
    "Estou no Mato Grosso, clima tropical",
    "Qual a dose para Lagarta do Cartucho?"
]

print("--- IA_Farm REAL MODE SIMULATION ---")
for q in queries:
    print(f"User: {q}")
    
    # Simple state extraction simulation from main.py
    for item in ["region", "climate"]:
        if f"{item}:" in q.lower() or "estou no" in q.lower():
            if "mato grosso" in q.lower(): session_state['region'] = "mato grosso"
            if "tropical" in q.lower(): session_state['climate'] = "tropical"

    response = orch.handle_request(q, session_state)
    print(f"AI: {response}\n")
