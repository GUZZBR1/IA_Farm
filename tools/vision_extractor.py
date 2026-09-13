import os
import json
import base64
import requests
from typing import List, Dict, Any, Optional

# Configuration
# In a real scenario, these would be environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your_api_key_here")
MODEL_NAME = "google/gemini-pro-vision" # Or "openai/gpt-4o" or "anthropic/claude-3.5-sonnet"

def encode_image(image_path: str) -> str:
    """Encodes an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_dosage_table(image_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extracts agricultural dosage table from an image using a Vision LLM.
    
    Args:
        image_path (str): Path to the image file.
        
    Returns:
        Optional[List[Dict[str, Any]]]: List of extracted rows as dictionaries, 
                                         or None if no table found or error occurs.
    """
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found.")
        return None

    base64_image = encode_image(image_path)

    prompt = (
        "You are an expert agricultural data extractor. Extract the dosage table from this image. "
        "Return ONLY a JSON list of objects. Each object must strictly follow this schema: "
        "{ \"crop\": \"string\", \"treatment\": \"string\", \"dosage\": \"string\", \"unit\": \"string\", \"frequency\": \"string\", \"notes\": \"string\" }. "
        "If no table is found, return an empty list []. "
        "Do not include markdown formatting like ```json ... ```, just the raw JSON array."
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        
        result_text = response.json()['choices'][0]['message']['content'].strip()
        
        # Clean potential markdown backticks if the LLM ignored instructions
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[-1].rsplit("\n", 1)[0]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        return json.loads(result_text)

    except Exception as e:
        print(f"Extraction Error: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) < 2:
        print("Usage: python vision_extractor.py <path_to_image>")
    else:
        img_path = sys.argv[1]
        data = extract_dosage_table(img_path)
        if data is not None:
            print(json.dumps(data, indent=2))
        else:
            print("Failed to extract data.")
