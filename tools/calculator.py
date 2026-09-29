"""Compatibility facade for deterministic dose arithmetic."""

from typing import Union

from tools.dosage_calculator import DosageError, calculate_total_dose


class DosageCalculator:
    """Calculate totals from an already validated dose per hectare.

    Agronomic recommendations are not inferred here. A caller must provide a
    validated value such as ``120kg/ha`` and the target area.
    """

    @staticmethod
    def calculate_total_dose(dose_per_hectare: Union[str, int, float], area_hectares) -> str:
        return calculate_total_dose(dose_per_hectare, area_hectares)

    @staticmethod
    def calculate_nitrogen_dose(dose_per_hectare, area_hectares) -> str:
        """Compatibility name; no agronomic dose is invented by this method."""

        return calculate_total_dose(dose_per_hectare, area_hectares)

    @staticmethod
    def validate_range(value, min_val, max_val) -> bool:
        return min_val <= value <= max_val


__all__ = ["DosageCalculator", "DosageError"]
