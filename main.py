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

from tools.orchastrator import Orchestrator


class MockVectorDB:
    def query(self, query, filters=None):
        return []

class SimulationInterface:
    def __init__(self):
        print("[SISTEMA] Inicializando componentes do IA_Farm...")
        if os.getenv("IA_FARM_MOCK") == "1":
            print("[SISTEMA] IA_FARM_MOCK=1; lógica determinística com base vazia de demonstração.")
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
        print("       🌾 IA_Farm — Referências técnicas sobre milho 🌾")
        print("                  Protótipo de simulação")
        print("="*60)
        print("\nO sistema consulta trechos locais com revisão registrada.")
        print("Não faz diagnóstico nem prescreve ou confirma doses.")
        print("\nComandos:")
        print("  - 'reset' : Limpar o contexto da sessão (região e clima)")
        print("  - 'exit'  : Encerrar a simulação")
        print("  - 'demo'  : Executar uma demonstração predefinida")
        print("-"*60)

    def process_input(self, user_input: str):
        # Visual feedback
        print("\n  [BUSCANDO REFERÊNCIAS LOCAIS...]", end="\r")
        time.sleep(0.3)
        
        response = self.orch.handle_request(user_input, self.session_state)
        print("  [RESPOSTA] ", end="")
        print(response)

    def run_demo(self):
        print("\n--- Iniciando modo de demonstração ---")
        demo_queries = [
            "Minha fazenda fica em Mato Grosso, com clima tropical.",
            "Qual informação sobre milho existe na base local?",
            "Como devo tratar uma praga nesta lavoura?"
        ]
        
        for i, q in enumerate(demo_queries, 1):
            print(f"\nPergunta de demonstração {i}: {q}")
            self.process_input(q)
            time.sleep(0.5)
        
        print("\n--- Demonstração concluída ---")
        print("Voltando ao modo interativo...")

    def start(self):
        self.greet()
        while self.is_running:
            try:
                user_input = input("\nVocê > ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit"]:
                    print("\nEncerrando a simulação. Até mais!")
                    self.is_running = False
                elif user_input.lower() == "reset":
                    self.session_state = {}
                    print("\n[SISTEMA] O contexto da sessão foi limpo.")
                elif user_input.lower() == "demo":
                    self.run_demo()
                else:
                    self.process_input(user_input)
            except EOFError:
                break
            except KeyboardInterrupt:
                print("\n\nSimulação interrompida. Encerrando...")
                break
            except Exception as e:
                print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    os.makedirs(PROJECT_ROOT / "data" / "vector_index", exist_ok=True)
    try:
        sim = SimulationInterface()
        sim.start()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        print("[ERROR] Install requirements.txt or set IA_FARM_MOCK=1 for a demo-only run.")
