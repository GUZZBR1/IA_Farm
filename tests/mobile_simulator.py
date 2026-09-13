
import sys
import time
import random
import os
from unittest.mock import MagicMock

# MOCKING MISSING LIBRARIES FOR SIMULATION
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['faiss'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['psutil'] = MagicMock() # avoid dependency on psutil for the sim

# Now import our real logic
sys.path.append('/home/guzzbr/meus-projetos/IA_Farm')
from tools.orchastrator import Orchestrator
from tools.vector_db import LocalVectorDB

class MobileHardwareSimulator:
    def __init__(self, ram_limit_gb=4.0):
        self.ram_limit = ram_limit_gb * 1024 * 1024 * 1024
        self.device_name = "Android Mid-Range (4GB RAM)"
        print(f"--- [HARDWARE SIMULATION ACTIVE: {self.device_name}] ---")
        print(f"System RAM Limit: {ram_limit_gb}GB | Mode: Low-Power / mmap Enabled\n")

    def simulate_latency(self, operation_type):
        latencies = {
            "embedding": (0.5, 1.5),
            "vector_search": (0.2, 0.8),
            "llm_token": (0.1, 0.3),
            "disk_io": (0.1, 0.4)
        }
        low, high = latencies.get(operation_type, (0.1, 0.5))
        time.sleep(random.uniform(low, high))

def run_simulation():
    sim = MobileHardwareSimulator()
    
    # Mocking the internal calls of the orchestrator to make the simulation fluid
    # and focused on the HARDWARE behavior rather than API availability.
    db = LocalVectorDB()
    orch = Orchestrator(vector_db_path="data/vector_index/")
    
    # Mocking the LLM to return deterministic and realistic agricultural responses
    def mock_llm_logic(prompt, **kwargs):
        if "Lamentamos" in prompt or "Antartida" in prompt:
            return "Lamentamos, mas não possuímos dados técnicos validados para a Antártida."
        if "To provide an accurate dosage" in prompt:
            return "Para fornecer a dose correta, preciso saber sua região e o clima local."
        if "caseira" in prompt:
            return "Como especialista da EMBRAPA, recomendo apenas práticas validadas cientificamente."
        return "Com base nos manuais da EMBRAPA, a dose recomendada para a Lagarta do Cartucho no Mato Grosso é de 2L/ha."

    orch._call_llm = mock_llm_logic

    scenarios = [
        {"name": "Boot & First Query", "query": "Qual a dose de NPK para milho?", "state": {}},
        {"name": "Regional Context", "query": "Estou no Mato Grosso, clima tropical", "state": {}},
        {"name": "Technical Query (RAG)", "query": "Qual a dose para Lagarta do Cartucho?", "state": {"region": "mato grosso", "climate": "tropical"}},
        {"name": "Cached Query (Speed Test)", "query": "Qual a dose para Lagarta do Cartucho?", "state": {"region": "mato grosso", "climate": "tropical"}}
    ]

    session_state = {}
    
    for s in scenarios:
        print(f"\n>>> Scenario: {s['name']}")
        print(f"Input: {s['query']}")
        
        sim.simulate_latency("disk_io") 
        start_time = time.time()
        
        # Actual logic call
        response = orch.handle_request(s['query'], session_state)
        
        # Simulating state extraction
        if "region:" in s['query'].lower() or "estou no" in s['query'].lower():
             session_state['region'] = "mato grosso"
             session_state['climate'] = "tropical"

        end_time = time.time()
        
        print(f"AI: {response}")
        print(f"Execution Time: {end_time - start_time:.2f}s")

if __name__ == '__main__':
    run_simulation()
