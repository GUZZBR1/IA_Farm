
import math

class DosageCalculator:
    @staticmethod
    def calculate_nitrogen_dose(target_yield, soil_content, efficiency=0.6):
        """
        Calculates Nitrogen dose based on simple formula: 
        Dose = (Target Yield * Factor) - (Soil Content * Factor)
        This is a placeholder for the actual agronomic formula.
        """
        try:
            # Example formula: Target (kg/ha) - Current (kg/ha)
            dose = (target_yield * 1.2) - (soil_content * 0.8)
            return max(0, round(dose, 2))
        except Exception as e:
            return f"Error in calculation: {e}"

    @staticmethod
    def validate_range(value, min_val, max_val):
        """Safety layer: checks if the dose is within safe limits."""
        return min_val <= value <= max_val
