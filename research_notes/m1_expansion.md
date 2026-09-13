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
