
import sys
from tools.orchastrator import Orchestrator
from tools.vector_db import LocalVectorDB

# Initialize the REAL components
db = LocalVectorDB()
orch = Orchestrator(vector_db_path='data/vector_index/')

session_state = {}

queries = [
    "Qual a dose de NPK para milho?",
    "estou no mato grosso, clima tropical",
    "Qual a dose para Lagarta do Cartucho?"
]

for q in queries:
    print(f"User: {q}")
    # We simulate the main.py logic
    # In main.py, the user input is checked for 'region:' or 'climate:'
    for item in ["region", "climate"]:
        if f"{item}:" in q.lower() or "estou no" in q.lower():
            if "mato grosso" in q.lower(): session_state['region'] = "mato grosso"
            if "tropical" in q.lower(): session_state['climate'] = "tropical"

    response = orch.handle_request(q, session_state)
    print(f"AI: {response}\n")
