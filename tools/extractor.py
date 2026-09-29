
import json
import os

class DataExtractor:
    def __init__(self, output_dir="data/structured_knowledge"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def process_table_to_json(self, source_name, raw_data):
        """
        Simulates the conversion of a PDF table to a structured JSON.
        In the full version, this would call a Vision LLM.
        """
        # Structured format: { "crop": "corn", "region": "SP", "soil": "clay", "dose": 120 }
        with open(f"{self.output_dir}/{source_name}.json", "w") as f:
            json.dump(raw_data, f, indent=4)
        return f"Saved {source_name} to JSON."

if __name__ == "__main__":
    ext = DataExtractor()
    # Mock data for testing
    mock_table = {
        "culture": "milho",
        "region": "Sudeste",
        "soil_type": "argiloso",
        "recommendations": {
            "nitrogen": {"low": 80, "medium": 120, "high": 150},
            "phosphorus": {"low": 40, "medium": 60, "high": 90}
        }
    }
    print(ext.process_table_to_json("embrapa_milho_v1", mock_table))
