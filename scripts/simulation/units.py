from enum import Enum
from sbmlpbkutils.unit_definitions import get_unit_type, UnitType
import libsbml as ls

class TimeUnit(str, Enum):
    SECOND = "seconds"
    MINUTE = "minutes"
    HOUR = "hours"
    DAY = "days"

    def __str__(self) -> str:
        return self.value

class AmountUnit(str, Enum):
    MICROGRAMS = "ug"
    MILLIGRAMS = "mg"
    GRAMS = "g"

    def __str__(self) -> str:
        return self.value

def get_model_time_unit(model: ls.Model) -> TimeUnit:
    """
    Extracts the model's time unit according to SBML rules:
    """

    unit_def_id = model.getTimeUnits()

    # Validate existence
    if not unit_def_id:
        raise Exception(
            f"Time unit not defined in model [{model.getId()}]."
        )

    unit_def = model.getUnitDefinition(unit_def_id)
    if unit_def is None:
        raise Exception(
            f"Time unit [{unit_def_id}] referenced in model [{model.getId()}] does not exist."
        )

    # Check whether this is a time unit
    if unit_def.getNumUnits() != 1:
        raise Exception(
            f"Time unit definition [{unit_def_id}] in model [{model.getId()}] "
            f"contains multiple unit elements, cannot interpret."
        )

    u = unit_def.getUnit(0)
    if u.getKind() != ls.UNIT_KIND_SECOND:
        raise Exception(
            f"UnitDefinition [{unit_def_id}] in model [{model.getId()}] "
            f"is not a valid time unit (kind={ls.UnitKind_toString(u.getKind())})."
        )

    # Check unit exponent: should be 1
    exponent = u.getExponent()
    if exponent != 1:
        raise Exception(
            f"Time unit [{unit_def_id}] exponent {exponent} is not supported."
        )

    # Get scale and multiplier (time unit = multiplier * second * 10^scale)
    scale = u.getScale()
    multiplier = u.getMultiplier()

    # First: pure second-based based on multiplier and scale
    base_seconds = multiplier * (10 ** scale)

    # Interpret units
    # Minute:   60 seconds
    # Hour:     3600 seconds
    # Day:      86400 seconds

    # Use tolerance for float rounding
    eps = 1e-10

    if abs(base_seconds - 1) < eps:
        return TimeUnit.SECOND
    elif abs(base_seconds - 60) < eps:
        return TimeUnit.MINUTE
    elif abs(base_seconds - 3600) < eps:
        return TimeUnit.HOUR
    elif abs(base_seconds - 86400) < eps:
        return TimeUnit.DAY
    else:
        raise Exception(
            f"Time unit [{unit_def_id}] in model [{model.getId()}] "
            f"has unsupported time conversion: {base_seconds} seconds."
        )

def get_model_amount_unit(model: ls.Model) -> AmountUnit:
    """
    Determine the substance/amount unit from an SBML model and map it to AmountUnit.
    """

    unit_def_id = model.getSubstanceUnits()

    if not unit_def_id:
        raise Exception(
            f"Substance (amount) unit not defined in model [{model.getId()}]."
        )

    unit_def = model.getUnitDefinition(unit_def_id)
    if unit_def is None:
        raise Exception(
            f"Substance unit [{unit_def_id}] referenced in model [{model.getId()}] does not exist."
        )

    if unit_def.getNumUnits() != 1:
        raise Exception(
            f"Substance unit definition [{unit_def_id}] in model [{model.getId()}] "
            f"has multiple unit elements; cannot interpret."
        )

    u = unit_def.getUnit(0)

    # Validate it is a substance amount unit (kilogram family)
    if u.getKind() != ls.UNIT_KIND_GRAM:
        raise Exception(
            f"UnitDefinition [{unit_def_id}] in model [{model.getId()}] "
            f"is not a mass/amount unit (kind={ls.UnitKind_toString(u.getKind())})."
        )

    # Extract SBML unit information
    multiplier = u.getMultiplier()  # typical: 1
    scale = u.getScale()            # log10 factor
    exponent = u.getExponent()      # should be 1

    if exponent != 1:
        raise Exception(
            f"Amount unit [{unit_def_id}] exponent {exponent} is unsupported."
        )

    # Compute actual grams represented (unit = multiplier * 10^scale grams)
    base_grams = multiplier * (10 ** scale)

    eps = 1e-12

    # Map to enum
    if abs(base_grams - 1e-6) < eps:
        return AmountUnit.MICROGRAMS
    elif abs(base_grams - 1e-3) < eps:
        return AmountUnit.MILLIGRAMS
    elif abs(base_grams - 1) < eps:
        return AmountUnit.GRAMS

    raise Exception(
        f"Amount unit [{unit_def_id}] in model [{model.getId()}] "
        f"maps to unsupported mass: {base_grams} grams."
    )

def get_time_unit_alignment_factor(
    model: ls.Model,
    target_unit: TimeUnit
) -> float:
    """
    Compute a conversion factor such that:

        time_in_target_units = time_in_model_units * factor

    The conversion is performed by converting both units to seconds.
    """

    # Resolve model time unit
    model_unit = get_model_time_unit(model)

    # Conversion map time unit to seconds
    map = {
        TimeUnit.SECOND: 1.0,
        TimeUnit.MINUTE: 60.0,
        TimeUnit.HOUR: 3600.0,
        TimeUnit.DAY: 86400.0,
    }

    if model_unit not in map:
        raise Exception(f"Unsupported model time unit: {model_unit}")

    if target_unit not in map:
        raise Exception(f"Unsupported target time unit: {target_unit}")

    model_seconds = map[model_unit]
    target_seconds = map[target_unit]
    return target_seconds / model_seconds

def get_amount_unit_alignment_factor(
    model: ls.Model,
    target_unit: AmountUnit
) -> float:
    """
    Compute a conversion factor such that:

        amount_in_target_units = amount_in_model_units * factor

    The conversion is performed by converting both units to grams.
    """

    # Resolve model amount unit
    model_unit = get_model_amount_unit(model)

    # Conversion map time unit to seconds
    map = {
        AmountUnit.GRAMS: 1.0,
        AmountUnit.MILLIGRAMS: 1e-3,
        AmountUnit.MICROGRAMS: 1e-6,
    }

    if model_unit not in map:
        raise Exception(f"Unsupported model amount unit: {model_unit}")

    if target_unit not in map:
        raise Exception(f"Unsupported target amount unit: {target_unit}")

    model_amount = map[model_unit]
    target_amount = map[target_unit]
    return model_amount / target_amount
