import re
import yaml
import json
from typing import Dict, List, Union, Any

# Taxonomy mapping based on docs/metadata_taxonomy.md
TAXONOMY = {
    "climate": {
        "Tropical": ["tropical", "equatorial", "hot and humid"],
        "Subtropical": ["subtropical", "mild winter"],
        "Temperate": ["temperate", "four seasons", "moderate climate"],
        "Semi-arid": ["semi-arid", "caatinga", "dry"],
        "Arid": ["arid", "desert"],
    },
    "region": {
        "Brazil-MatoGrosso": ["matogrosso", "mt", "cerrado"],
        "Brazil-Parana": ["parana", "pr", "south of brazil"],
        "Brazil-SaoPaulo": ["saopaulo", "sp"],
        "Brazil-MinasGerais": ["minasgerais", "mg"],
        "Brazil-Bahia": ["bahia", "ba"],
        "Global-NorthAmerica": ["north america", "usa", "canada"],
    },
    "soil": {
        "Latossolo": ["latossolo", "oxisol"],
        "Argissolo": ["argissolo", "ultisol"],
        "Neossolo": ["neossolo", "entisol"],
        "Vertissolo": ["vertissolo", "vertisol"],
    },
    "season": {
        "Safra": ["safra", "main crop", "primary harvest"],
        "Safrinha": ["safrinha", "second crop", "off-season"],
        "Winter": ["winter", "inverno"],
        "Summer": ["summer", "verao"],
    }
}

def suggest_tags(content: Union[str, Dict]) -> Dict[str, List[str]]:
    """
    Suggests metadata tags based on keywords found in the content.
    """
    if isinstance(content, dict):
        text = " ".join(str(v) for v in content.values()).lower()
    else:
        text = content.lower()

    suggested_metadata = {}

    for category, mapping in TAXONOMY.items():
        matches = []
        for tag, keywords in mapping.items():
            if any(keyword in text for keyword in keywords):
                matches.append(tag)
        
        if matches:
            suggested_metadata[category] = matches

    return suggested_metadata

def format_as_yaml_header(metadata: Dict[str, List[str]]) -> str:
    """
    Formats the metadata dictionary into a YAML frontmatter header.
    """
    # Convert lists to comma-separated strings or single values for simplicity in YAML
    processed_metadata = {}
    for k, v in metadata.items():
        processed_metadata[k] = v[0] if len(v) == 1 else v

    yaml_content = yaml.dump(processed_metadata, default_flow_style=False)
    return f"---\n{yaml_content}---"

def process_content(content: Union[str, Dict]) -> str:
    """
    Analyzes content, suggests tags, and prepends the YAML header to the text.
    """
    tags = suggest_tags(content)
    header = format_as_yaml_header(tags)
    
    text_body = content if isinstance(content, str) else json.dumps(content, indent=2)
    return f"{header}\n\n{text_body}"

if __name__ == "__main__":
    # Test cases
    test_texts = [
        "The corn dosage for the Safra season in Mato Grosso Cerrado soils (Latossolo) under Tropical climate.",
        "Recommendations for soybean Safrinha in Parana with Subtropical conditions."
    ]
    
    for t in test_texts:
        print(f"Input: {t}")
        print(process_content(t))
        print("-" * 20)
