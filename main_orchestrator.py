
from tools.memory_manager import MemoryManager
from tools.vector_engine import VectorEngine
from tools.calculator import DosageCalculator
import json

class AgriBrainOrchestrator:
    def __init__(self, api_key):
        self.mem = MemoryManager()
        self.vec = VectorEngine(api_key=api_key)
        self.calc = DosageCalculator()

    def handle_query(self, query):
        # 1. Get user context (Soil, Region)
        context = self.mem.get_all_profile_context()
        
        # 2. Search Technical Knowledge (RAG)
        tech_docs = self.vec.search(query)
        
        # 3. Decision Logic: Is it a dosage query?
        if "dose" in query.lower() or "quanto de" in query.lower():
            # In a real scenario, the LLM would extract 'target_yield' and 'soil_content'
            # Here we simulate the extraction
            target_yield = 120 # extracted from query
            soil_content = 30  # extracted from memory/query
            
            dose = self.calc.calculate_nitrogen_dose(target_yield, soil_content)
            return f"Based on your soil ({context}), the deterministic dose is {dose} kg/ha."
        
        return "I can help you with general agricultural info or precise dosage."

if __name__ == "__main__":
    # Basic test (API key would be needed for real vector search)
    orch = AgriBrainOrchestrator(api_key="mock_key")
    print(orch.handle_query("Qual a dose de N para meu solo?"))
