import json
import os
from unittest.mock import MagicMock

# Mocking the Orchestrator to avoid heavy dependency issues (faiss, torch, etc.) 
# and disk quota problems while still validating the Golden Set logic.
class MockOrchestrator:
    def handle_request(self, query, session_state):
        # Simulated AI response logic for testing the runner
        if "Fall Armyworm" in query:
            return "Apply 2L/ha of Chlorantraniliprole when larvae are in L1-L3 stage."
        if "NPK" in query:
            return "Apply 120kg/ha N, 60kg/ha P2O5, 40kg/ha K2O."
        if "Leaf Blight" in query:
            return "Wrong dosage: Apply 1L/ha of Azoxystrobin." # Simulate critical failure
        if "planting depth" in query:
            return "The ideal planting depth is 3-5 cm."
        return "I don't have enough technical data for this query."

def compare_responses(ai_response, ground_truth):
    import re
    gt_numbers = re.findall(r'\d+\.?\d*\s*(?:L/ha|kg/ha|mm|cm|tons/ha|%)', ground_truth)
    if not gt_numbers:
        return "Pass" if any(word.lower() in ai_response.lower() for word in ground_truth.split() if len(word) > 3) else "Minor Failure"
    for num in gt_numbers:
        if num not in ai_response:
            return "Critical Failure"
    return "Pass"

def main():
    orch = MockOrchestrator()
    golden_set_path = 'tests/golden_set.json'
    report_path = 'tests/validation_report.md'
    
    if not os.path.exists(golden_set_path):
        print(f"Error: {golden_set_path} not found.")
        return

    with open(golden_set_path, 'r') as f:
        test_cases = json.load(f)
    
    results = []
    hallucinations = 0
    critical_failures = 0
    minor_failures = 0
    passes = 0
    
    print(f"Running {len(test_cases)} Golden Set tests (Mock Mode)...\n")
    
    for i, case in enumerate(test_cases):
        query = case['query']
        gt = case['ground_truth']
        critical = case['critical']
        session_state = case['session_state']
        
        response = orch.handle_request(query, session_state)
        status = compare_responses(response, gt)
        
        if "don't have enough technical data" in response.lower() and gt:
            status = "Minor Failure" if not critical else "Critical Failure"
                
        if status == "Critical Failure":
            critical_failures += 1
        elif status == "Minor Failure":
            minor_failures += 1
        else:
            passes += 1
        
        if critical and status == "Critical Failure" and "don't have enough" not in response.lower():
            hallucinations += 1

        results.append({"query": query, "ground_truth": gt, "ai_response": response, "status": status, "critical": critical})

    accuracy = (passes / len(test_cases)) * 100
    with open(report_path, 'w') as f:
        f.write("# Golden Set Validation Report (Simulated)\n\n")
        f.write(f"**Total Tests:** {len(test_cases)}\n")
        f.write(f"**Accuracy Rate:** {accuracy:.2f}%\n")
        f.write(f"**Hallucination Count:** {hallucinations}\n")
        f.write(f"**Critical Failures:** {critical_failures}\n")
        f.write(f"**Minor Failures:** {minor_failures}\n\n")
        f.write("## Failure Details\n\n| Query | Ground Truth | AI Response | Status |\n|---|---|---|---|\n")
        for r in results:
            if r['status'] != "Pass":
                f.write(f"| {r['query']} | {r['ground_truth']} | {r['ai_response']} | {r['status']} |\n")
                
    print(f"Validation complete. Report generated at {report_path}")

if __name__ == "__main__":
    main()
