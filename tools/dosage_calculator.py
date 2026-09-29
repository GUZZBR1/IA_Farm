"""Deterministic, unit-aware arithmetic for already-validated agronomic doses."""

import re
from decimal import Decimal, InvalidOperation
from typing import Union


Number = Union[str, int, float, Decimal]
DOSE_RE = re.compile(r"^\s*(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>[a-zA-Zµ]+(?:/[a-zA-Z]+)?)?\s*$")


class DosageError(ValueError):
    """Raised when a dose or area is invalid for deterministic calculation."""


def _decimal(value: Number, field: str) -> Decimal:
    try:
        result = Decimal(str(value).replace(",", ".").strip())
    except (InvalidOperation, ValueError):
        raise DosageError(f"{field} must be numeric") from None
    if result <= 0:
        raise DosageError(f"{field} must be greater than zero")
    return result


def parse_dose_per_hectare(value: Number) -> tuple[Decimal, str]:
    """Parse values such as ``120kg/ha`` while preserving the unit."""

    match = DOSE_RE.match(str(value))
    if not match:
        raise DosageError("dose must look like '120kg/ha' or a positive number")

    amount = _decimal(match.group("value"), "dose")
    unit = match.group("unit") or "unit/ha"
    if "/ha" not in unit.casefold():
        raise DosageError("dose must be expressed per hectare")
    return amount, unit


def calculate_total_dose(dose_per_hectare: Number, area_hectares: Number) -> str:
    """Calculate the total amount for a given area without calling an LLM."""

    dose, unit = parse_dose_per_hectare(dose_per_hectare)
    area = _decimal(area_hectares, "area")
    total = dose * area
    base_unit = unit.rsplit("/", 1)[0]
    return f"{format(total.normalize(), 'f')} {base_unit}"
