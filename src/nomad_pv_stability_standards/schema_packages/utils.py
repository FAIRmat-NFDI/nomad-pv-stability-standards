"""Helpers of the schema package that do not depend on its sections: annotations
and the quantities that every variable repeats."""

from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.metainfo import Quantity


def eln(component: ELNComponentEnum) -> ELNAnnotation:
    return ELNAnnotation(component=component)


def limit(end: str, unit: str, display_unit: str | None = None) -> Quantity:
    """The lowest or highest value of a variable. The minimum and the maximum are equal
    where the standard gives a single value."""
    return Quantity(
        type=float,
        unit=unit,
        description=f'The {end} value; equal to the other limit for a single value.',
        a_eln=eln(ELNComponentEnum.NumberEditQuantity),
        a_display={'unit': display_unit} if display_unit else None,
    )
