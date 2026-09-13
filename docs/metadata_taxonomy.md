# Agricultural Metadata Taxonomy

This document defines the standardized tags used across the IA_Farm knowledge base to ensure consistency in agricultural recommendations.

## 1. Climate Zones (`climate`)
- `Tropical`: High temperature, high rainfall throughout the year.
- `Subtropical`: Distinct seasons, mild winters, warm summers.
- `Temperate`: Moderate climate with clear four-season distinction.
- `Semi-arid`: Low and irregular rainfall, high evaporation rates.
- `Arid`: Extremely dry regions.

## 2. Regional Tags (`region`)
- `Brazil-MatoGrosso`: High productivity, Cerrado influence.
- `Brazil-Parana`: South region, subtropical, strong corn/soy belt.
- `Brazil-SaoPaulo`: Diverse agriculture, temperate/subtropical.
- `Brazil-MinasGerais`: Coffee and diverse livestock.
- `Brazil-Bahia`: Mixed semi-arid and tropical zones.
- `Global-NorthAmerica`: Temperate agriculture.

## 3. Soil Types (`soil`)
- `Latossolo`: Deep, highly weathered, typical of Cerrado.
- `Argissolo`: Distinct clay accumulation in lower horizons.
- `Neossolo`: Young soils, less developed.
- `Vertissolo`: High clay content, shrinking/swelling properties.

## 4. Seasonality (`season`)
- `Safra`: Main harvest season.
- `Safrinha`: Second harvest/off-season crop.
- `Winter`: Cold season planting/growth.
- `Summer`: Warm season planting/growth.

## Usage Example (YAML Frontmatter)
```yaml
---
climate: Tropical
region: Brazil-MatoGrosso
soil: Latossolo
season: Safra
---
```
