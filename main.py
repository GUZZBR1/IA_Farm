import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# The mock is available only when explicitly requested with IA_FARM_MOCK=1.

from tools.metadata import canonicalize
from tools.orchastrator import Orchestrator


class MockVectorDB:
    def query(self, query, filters=None):
        return []

class SimulationInterface:
    def __init__(self):
        print("[SYSTEM] Initializing IA_Farm Components...")
        if os.getenv("IA_FARM_MOCK") == "1":
            print("[SYSTEM] IA_FARM_MOCK=1; running real deterministic logic with an empty fixture database.")
            self.orch = Orchestrator(db=MockVectorDB())
        else:
            self.orch = Orchestrator(vector_db_path=str(PROJECT_ROOT / "data" / "vector_index"))
        
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
                    self.session_state[key] = canonicalize(key, value)
                    print(f"  [STATE UPDATE] {key.capitalize()} set to: {self.session_state[key]}")
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
    os.makedirs(PROJECT_ROOT / "data" / "vector_index", exist_ok=True)
    try:
        sim = SimulationInterface()
        sim.start()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        print("[ERROR] Install requirements.txt or set IA_FARM_MOCK=1 for a demo-only run.")
