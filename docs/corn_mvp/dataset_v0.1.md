# 🌽 Corn Dataset v0.1 - Technical Knowledge Base

## 🟢 Module C: Phytosanitary (Pests & Diseases)

### [Pest: Spodoptera frugiperda (Lagarta-do-cartucho)]
- **Metadata:** { "region": "National", "severity": "High", "type": "Lepidoptera" }
- **Symptoms:**
    - Early stage: Small holes in leaves (windowpane effect).
    - Advanced stage: Large irregular holes and sawdust-like frass in the whorl.
- **Triagem Flow:**
    1. Are there holes in the leaves? (Yes/No)
    2. Is there sawdust-like debris in the whorl? (Yes/No)
    3. If both YES -> High probability of Spodoptera frugiperda.
- **Control (Deterministic Dosage):**
```json
{
  "treatment": "Chemical Control",
  "product": "Chlorantraniliprole",
  "dosage_pair": {
    "standard_dose": "50ml/ha",
    "condition": "Average infestation",
    "application": "Foliar spray"
  }
}
```

### [Pest: Dalbulus maidis (Cigarrinha-do-milho)]
- **Metadata:** { "region": "National", "severity": "Critical", "type": "Hemiptera" }
- **Symptoms:**
    - Yellowing of leaves (chlorosis).
    - Stunting of the plant.
    - Presence of small yellow insects on the underside of leaves.
- **Triagem Flow:**
    1. Are the leaves yellowing from the bottom up? (Yes/No)
    2. Is the plant shorter than usual for its age? (Yes/No)
    3. If both YES -> High probability of Dalbulus maidis / Maize Stunt.
- **Control (Deterministic Dosage):**
```json
{
  "treatment": "Chemical Control",
  "product": "Neonicotinoids",
  "dosage_pair": {
    "standard_dose": "Variable by product",
    "condition": "Early detection",
    "application": "Seed treatment or Foliar"
  }
}
```

## 🔵 Module A: Soil & Nutrition (Baseline)

### [Nutrient: Nitrogen (N)]
- **Metadata:** { "region": "General", "type": "Macronutrient" }
- **Symptom:** V-shaped yellowing starting from the tip of older leaves.
- **Dose Pairing:**
```json
{
  "nutrient": "Nitrogen",
  "target_yield": "120 bags/ha",
  "dose_pair": {
    "standard_dose": "120kg/ha",
    "split": "50% planting, 50% top-dressing",
    "condition": "Medium soil organic matter"
  }
}
```
# 🌽 Corn Dataset v0.2 - Expansion
## 🟢 Module C: Phytosanitary (Pests & Diseases)

### [Disease: Rust (Ferrugem Polissora)]
- **Metadata:** { "region": "National", "severity": "High", "type": "Fungal" }
- **Symptoms:**
    - Small orange-brown pustules on leaf surfaces.
    - Premature leaf drying (necrosis).
- **Triagem Flow:**
    1. Are there orange pustules on the leaves? (Yes/No)
    2. Is the plant showing premature drying? (Yes/No)
    3. If both YES -> High probability of Rust.
- **Control (Deterministic Dosage):**
```json
{
  "treatment": "Fungicide",
  "product": "Triazoles/Strobilurins",
  "dosage_pair": {
    "standard_dose": "0.5L/ha",
    "condition": "Preventive application",
    "application": "Foliar spray"
  }
}
```

## 🔵 Module A: Soil & Nutrition
### [Nutrient: Zinc (Zn)]
- **Metadata:** { "region": "General", "type": "Micronutrient" }
- **Symptom:** Chlorosis in the whorl (white/yellow streaks) in young plants.
- **Dose Pairing:**
```json
{
  "nutrient": "Zinc",
  "target_yield": "Standard",
  "dose_pair": {
    "standard_dose": "2kg/ha (as ZnSO4)",
    "condition": "Deficient soil",
    "application": "Seed treatment or Foliar"
  }
}
```
