"""PV stability standards, such as the ISOS protocols, as NOMAD entries."""

from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.results import ELN
from nomad.metainfo import MEnum, Quantity, SchemaPackage, SubSection

m_package = SchemaPackage()

CONTROL = {
    'ambient': 'Not influenced: the value of the surroundings.',
    'specified': """
        The standard requires a value or a limit, but not how it is kept, e.g. a
        relative humidity below 50 %.""",
    'set': 'A setpoint, applied without feedback.',
    'controlled': 'Held at the setpoint by feedback.',
    'tracked': 'Follows a point of the device, given as the target, e.g. the MPP.',
    'swept': 'Driven from the minimum to the maximum, e.g. in a J–V scan.',
    'cycled': 'Alternates between the minimum and the maximum.',
}

LIGHT = {
    'dark': 'No light.',
    'solar_simulator': 'Light from a solar simulator.',
    'sunlight': 'Natural sunlight, outdoors.',
}


def _edit(component: ELNComponentEnum) -> ELNAnnotation:
    return ELNAnnotation(component=component)


def _limit(end: str, unit: str, display_unit: str | None = None) -> Quantity:
    """The lowest or highest value of a variable. The minimum and the maximum are equal
    where the standard gives a single value."""
    return Quantity(
        type=float,
        unit=unit,
        description=f'The {end} value; equal to the other limit for a single value.',
        a_eln=_edit(ELNComponentEnum.NumberEditQuantity),
        a_display={'unit': display_unit} if display_unit else None,
    )


class Variable(ArchiveSection):
    """
    A physical variable of a test, such as the temperature or the voltage: how the
    standard fixes its value, and whether it is recorded during the test. A variable
    the standard does not mention stays empty.
    """

    control = Quantity(
        type=MEnum(*CONTROL, m_descriptions=CONTROL),
        description='How the value is fixed.',
        a_eln=_edit(ELNComponentEnum.EnumEditQuantity),
    )
    monitored = Quantity(
        type=bool,
        description='Whether the variable is recorded during the test.',
        a_eln=_edit(ELNComponentEnum.BoolEditQuantity),
    )
    target = Quantity(
        type=str,
        description="""
        A value defined by the device rather than by a number, e.g. `MPP`, `V_oc`,
        `-V_oc` or `-J_MPP`.
        """,
        a_eln=_edit(ELNComponentEnum.StringEditQuantity),
    )


class Temperature(Variable):
    """The temperature of the device."""

    minimum = _limit('lowest', 'K', 'celsius')
    maximum = _limit('highest', 'K', 'celsius')


class Irradiance(Variable):
    """The irradiance on the device."""

    minimum = _limit('lowest', 'W/m^2')
    maximum = _limit('highest', 'W/m^2')


class Voltage(Variable):
    """The voltage across the device."""

    minimum = _limit('lowest', 'V')
    maximum = _limit('highest', 'V')


class CurrentDensity(Variable):
    """The current density through the device."""

    minimum = _limit('lowest', 'A/m^2', 'mA/cm^2')
    maximum = _limit('highest', 'A/m^2', 'mA/cm^2')


class RelativeHumidity(Variable):
    """The relative humidity of the atmosphere, as a fraction: 0.5 for 50 %."""

    minimum = _limit('lowest', 'dimensionless')
    maximum = _limit('highest', 'dimensionless')


class OxygenFraction(Variable):
    """The oxygen content of the atmosphere, as a fraction: 0.21 for air."""

    minimum = _limit('lowest', 'dimensionless')
    maximum = _limit('highest', 'dimensionless')


class Condition(ArchiveSection):
    """
    Variables that are applied together, with a common timing. A condition without
    period lasts for the whole test. Conditions of the same kind may overlap in
    time, e.g. a periodic J–V scan during MPP tracking; how they combine is up to
    the standard and is described in its notes.
    """

    period = Quantity(
        type=float,
        unit='s',
        description='The condition repeats every period. Empty: it lasts throughout.',
        a_eln=_edit(ELNComponentEnum.NumberEditQuantity),
        a_display={'unit': 'hour'},
    )
    active_duration = Quantity(
        type=float,
        unit='s',
        description="""
        How long the condition lasts in each period, e.g. 12 h of light in a 24 h
        light–dark cycle.
        """,
        a_eln=_edit(ELNComponentEnum.NumberEditQuantity),
        a_display={'unit': 'hour'},
    )
    notes = Quantity(
        type=str,
        description='What the standard says about this condition beyond its values.',
        a_eln=_edit(ELNComponentEnum.RichTextEditQuantity),
    )


class Thermal(Condition):
    """The temperature of the device."""

    temperature = SubSection(section_def=Temperature)


class OptoElectrical(Condition):
    """The light on the device and its electrical state, which act together."""

    light = Quantity(
        type=MEnum(*LIGHT, m_descriptions=LIGHT),
        description='The light the device is exposed to.',
        a_eln=_edit(ELNComponentEnum.EnumEditQuantity),
    )
    irradiance = SubSection(section_def=Irradiance)
    voltage = SubSection(section_def=Voltage)
    current_density = SubSection(section_def=CurrentDensity)


class Atmosphere(Condition):
    """The gas around the device and its humidity and oxygen content."""

    gas = Quantity(
        type=str,
        description='The gas around the device, e.g. `air`, `N2` or `Ar`.',
        a_eln=_edit(ELNComponentEnum.StringEditQuantity),
    )
    relative_humidity = SubSection(section_def=RelativeHumidity)
    oxygen_fraction = SubSection(section_def=OxygenFraction)


class StabilityStandard(EntryData):
    """
    A PV stability standard, or one variant of it: the conditions under which a
    stability test is run, as a standard such as the ISOS protocols fixes them.

    A standard that offers options, such as 65 °C or 85 °C, has one entry per
    combination of options, its variants.
    """

    name = Quantity(
        type=str,
        description='The name of the standard as it writes it, e.g. `ISOS-L-2`.',
        a_eln=_edit(ELNComponentEnum.StringEditQuantity),
    )
    variant = Quantity(
        type=str,
        description="""
        The options of the standard that this entry takes, separated by commas, e.g.
        `65 °C, MPP`. Empty where the entry takes no option.
        """,
        a_eln=_edit(ELNComponentEnum.StringEditQuantity),
    )
    reference = Quantity(
        type=str,
        description='The publication of the standard, e.g. as a DOI link.',
        a_eln=_edit(ELNComponentEnum.URLEditQuantity),
    )
    notes = Quantity(
        type=str,
        description="""
        How the standard's text was read: quotes, options the standard leaves open,
        and what it does not state.
        """,
        a_eln=_edit(ELNComponentEnum.RichTextEditQuantity),
    )
    conditions = SubSection(
        section_def=Condition,
        repeats=True,
        description='The conditions of the test: thermal, opto-electrical, atmosphere.',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Names the entry after the standard and, in parentheses, its variant, e.g.
        `ISOS-L-2 (65 °C, MPP)`, and makes the standard's name one of the methods by
        which NOMAD's apps find entries."""
        super().normalize(archive, logger)

        self.name = self.name.strip() if self.name else None
        self.variant = self.variant.strip() if self.variant else None
        if self.name is None:
            return

        if archive.metadata is not None:
            archive.metadata.entry_name = (
                f'{self.name} ({self.variant})' if self.variant else self.name
            )
        if archive.results is not None:
            if archive.results.eln is None:
                archive.results.eln = ELN()
            archive.results.eln.methods = [self.name]


m_package.__init_metainfo__()
