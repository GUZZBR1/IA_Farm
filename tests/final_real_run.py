
import sys
import os
import time

# Set path to root for imports
sys.path.append('/home/guzzbr/meus-projetos/IA_Farm')

try:
    from tools.orchastrator import Orchestrator
    from tools.vector_db import LocalVectorDB
    print("[SISTEMA] Bibliotecas carregadas com sucesso.")
except ImportError as e:
    print(f"[ERRO] Falha ao carregar ferramentas: {e}")
    sys.exit(1)

# Initialize the REAL components
print("[SISTEMA] Inicializando Vector DB e Orquestrador...")
db = LocalVectorDB()
orch = Orchestrator(vector_db_//db_path='data/vector_index/')
print("[SISTEMA] Componentes prontos.\n")

session_state = {}

queries = [
    "Qual a dose de NPK para milho?",
    "Estou no Mato Grosso, clima tropical",
    "Qual a dose para Lagarta do Cartucho?"
]

print("--- IA_Farm REAL MODE SIMULATION ---")
for q in queries:
    print(f"User: {q}")
    
    # Simulating the main.py logic for state extraction
    for item in ["region", "climate"]:
        if f"{item}:" in q.lower() or "estou no" in q.lower():
            if "mato grosso" in q.lower(): session_state['region'] = "mato grosso"
            if "tropical" in q.lower(): session_state['climate'] = "tropical"

    start_time = time.time()
    response = orch.handle_request(q, session_state)
    end_time = time.time()
    
    print(f"AI: {response}")
    print(f"Time: {end_time - start_time:.2f}s\n")
