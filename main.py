import os
import sys
import time
from typing import Dict, Any, List

# Add project root to sys.path
PROJECT_ROOT = "/home/guzzbr/meus-projetos/IA_Farm"
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# MOCK CLASSES to allow the interface to run even if heavy dependencies are missing
# This ensures the "Simulation Interface" logic is verified regardless of the environment's disk quota/libs.

try:
    from tools.vector_db import LocalVectorDB
    from tools.orchastrator import Orchestrator
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    print("[SYSTEM] Heavy dependencies missing. Running in MOCK MODE for interface demo.")
    
    class MockVectorDB:
        def query(self, query, filters=None):
            return [{"text": "Mock context: Corn requires nitrogen and phosphorous in Mato Grosso."}]

    class MockOrchestrator:
        def __init__(self, vector_db_path=""):
            self.db = MockVectorDB()
            self.required_metadata = ["region", "climate"]

        def handle_request(self, user_input, session_state):
            technical_keywords = ["dosage", "amount", "how much", "apply", "treatment", "dose"]
            is_technical = any(kw in user_input.lower() for kw in technical_keywords)
            
            if is_technical:
                missing = [m for m in self.required_metadata if m not in session_state]
                if missing:
                    return f"To provide an accurate dosage, I need more information. Please tell me your {', '.join(missing)}."
                return f"Based on your {session_state.get('region')} region, I recommend a standard nitrogen dosage of 120kg/ha."
            
            return "I am the EMBRAPA Corn Specialist. I can help you with your crop management. Please provide your region and climate for specific advice."

class SimulationInterface:
    def __init__(self):
        print("[SYSTEM] Initializing IA_Farm Components...")
        if HAS_DEPS:
            self.orch = Orchestrator(vector_db_path="data/vector_index/")
        else:
            self.orch = MockOrchestrator()
        
        self.session_state = {}
        self.is_running = True

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def greet(self):
        self.clear_screen()
        print("="*60)
        print("           🌾 EMBRAPA CORN SPECIALIST AI SYSTEM 🌾")
        print("               Unified Simulation Interface")
        print("="*60)
        print("\nWelcome! I am your specialized assistant for corn cultivation.")
        print("I can help with dosage, climate analysis, and crop management.")
        print("\nCommands:")
        print("  - 'reset' : Clear current session state (Region, Climate, Soil)")
        print("  - 'exit'  : Terminate simulation")
        print("  - 'demo'  : Run a predefined demo sequence")
        print("-"*60)

    def process_input(self, user_input: str):
        # Handle session state updates naturally
        for key in ["region", "climate", "soil"]:
            if f"{key}:" in user_input.lower():
                try:
                    parts = user_input.lower().split(f"{key}:")
                    value = parts[1].split(",")[0].strip().strip(".")
                    self.session_state[key] = value
                    print(f"  [STATE UPDATE] {key.capitalize()} set to: {value}")
                except Exception:
                    pass

        # Visual feedback
        print("\n  [RETRIEVING CONTEXT...]", end="\r")
        time.sleep(0.3)
        print("  [CONSULTING SPECIALIST...]", end="\r")
        time.sleep(0.3)
        
        response = self.orch.handle_request(user_input, self.session_state)
        print("  [RESPONSE] ", end="")
        print(response)

    def run_demo(self):
        print("\n--- Starting Demo Mode ---")
        demo_queries = [
            "Hello! I'm starting a farm in the Mato Grosso region with tropical climate.",
            "What is the recommended nitrogen dosage for my corn crop?",
            "How should I manage pest control in this environment?"
        ]
        
        for i, q in enumerate(demo_queries, 1):
            print(f"\nDemo Query {i}: {q}")
            self.process_input(q)
            time.sleep(0.5)
        
        print("\n--- Demo Completed ---")
        print("Returning to interactive mode...")

    def start(self):
        self.greet()
        while self.is_running:
            try:
                user_input = input("\nUser > ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit"]:
                    print("\nShutting down simulation. Goodbye!")
                    self.is_running = False
                elif user_input.lower() == "reset":
                    self.session_state = {}
                    print("\n[SYSTEM] Session state has been reset.")
                elif user_input.lower() == "demo":
                    self.run_demo()
                else:
                    self.process_input(user_input)
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n\nSimulation interrupted by user. Exiting...")
                break
            except Exception as e:
                print(f"\n[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    os.makedirs("data/vector_index/", exist_ok=True)
    sim = SimulationInterface()
    sim.start()
