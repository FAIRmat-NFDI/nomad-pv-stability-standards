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
from nomad.datamodel.metainfo.annotations import ELNComponentEnum
from nomad.datamodel.metainfo.plot import PlotSection
from nomad.datamodel.results import ELN
from nomad.metainfo import URL, MEnum, MProxy, Quantity, SchemaPackage, SubSection

from nomad_pv_stability_standards.schema_packages.plotting_channels import (
    timeline_figures,
)
from nomad_pv_stability_standards.schema_packages.utils import eln, limit

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


class Variable(ArchiveSection):
    """
    A physical variable of a test, such as the temperature or the voltage: how the
    standard fixes its value, and whether it is recorded during the test. A variable
    the standard does not mention stays empty.
    """

    control = Quantity(
        type=MEnum(*CONTROL, m_descriptions=CONTROL),
        description='How the value is fixed.',
        a_eln=eln(ELNComponentEnum.EnumEditQuantity),
    )
    monitored = Quantity(
        type=bool,
        description='Whether the variable is recorded during the test.',
        a_eln=eln(ELNComponentEnum.BoolEditQuantity),
    )
    target = Quantity(
        type=str,
        description="""
        A named value instead of, or beside, a number: a point of the device, e.g.
        `MPP`, `V_oc`, `-V_oc` or `-J_MPP`, or a named condition, e.g. `RT`.
        """,
        a_eln=eln(ELNComponentEnum.StringEditQuantity),
    )


class Temperature(Variable):
    """A temperature: of the device in the thermal channel, of the gas around it in
    the atmosphere channel."""

    minimum = limit('lowest', 'K', 'celsius')
    maximum = limit('highest', 'K', 'celsius')


class Irradiance(Variable):
    """The irradiance on the device."""

    minimum = limit('lowest', 'W/m^2')
    maximum = limit('highest', 'W/m^2')


class Voltage(Variable):
    """The voltage across the device."""

    minimum = limit('lowest', 'V')
    maximum = limit('highest', 'V')


class CurrentDensity(Variable):
    """The current density through the device."""

    minimum = limit('lowest', 'A/m^2', 'mA/cm^2')
    maximum = limit('highest', 'A/m^2', 'mA/cm^2')


class RelativeHumidity(Variable):
    """The relative humidity of the atmosphere, as a fraction: 0.5 for 50 %."""

    minimum = limit('lowest', 'dimensionless')
    maximum = limit('highest', 'dimensionless')


class OxygenFraction(Variable):
    """The oxygen content of the atmosphere, as a fraction: 0.21 for air."""

    minimum = limit('lowest', 'dimensionless')
    maximum = limit('highest', 'dimensionless')


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
        description="""
        The condition repeats every period. Empty: it lasts throughout, unless its notes
        say that it repeats at an interval the standard does not state.
        """,
        a_eln=eln(ELNComponentEnum.NumberEditQuantity),
        a_display={'unit': 'hour'},
    )
    active_duration = Quantity(
        type=float,
        unit='s',
        description="""
        How long the condition lasts in each period, e.g. 12 h of light in a 24 h
        light–dark cycle.
        """,
        a_eln=eln(ELNComponentEnum.NumberEditQuantity),
        a_display={'unit': 'hour'},
    )
    notes = Quantity(
        type=str,
        description='What the standard says about this condition beyond its values.',
        a_eln=eln(ELNComponentEnum.RichTextEditQuantity),
    )


class Thermal(Condition):
    """The temperature of the device."""

    temperature = SubSection(
        section_def=Temperature, description='The temperature of the device.'
    )


class OptoElectrical(Condition):
    """The light on the device and its electrical state, which act together."""

    light = Quantity(
        type=MEnum(*LIGHT, m_descriptions=LIGHT),
        description='The light the device is exposed to.',
        a_eln=eln(ELNComponentEnum.EnumEditQuantity),
    )
    irradiance = SubSection(section_def=Irradiance)
    voltage = SubSection(section_def=Voltage)
    current_density = SubSection(section_def=CurrentDensity)


class Atmosphere(Condition):
    """The gas around the device: its temperature, humidity and oxygen content."""

    gas = Quantity(
        type=str,
        description='The gas around the device, e.g. `air`, `N2` or `Ar`.',
        a_eln=eln(ELNComponentEnum.StringEditQuantity),
    )
    temperature = SubSection(
        section_def=Temperature,
        description="""
        The temperature of the gas, e.g. of an environmental chamber. It may differ
        from the device's, which heats under light, and together with
        `relative_humidity` it gives the absolute humidity.
        """,
    )
    relative_humidity = SubSection(section_def=RelativeHumidity)
    oxygen_fraction = SubSection(section_def=OxygenFraction)


class Conditions(ArchiveSection):
    """The conditions of a test, in three channels."""

    thermal_channel = SubSection(
        section_def=Thermal,
        repeats=True,
        description='The thermal channel of the test.',
    )
    opto_electrical_channel = SubSection(
        section_def=OptoElectrical,
        repeats=True,
        description="""
        The opto-electrical channel of the test. The channel represents both stress
        and characterization, e.g. MPP tracking under light and, overlapping it, a
        periodic J–V scan.
        """,
    )
    atmosphere_channel = SubSection(
        section_def=Atmosphere,
        repeats=True,
        description='The atmosphere channel of the test.',
    )


class StabilityStandard(PlotSection, EntryData, Conditions):
    """
    A PV stability standard: the conditions under which a stability test is run, as a
    standard such as the ISOS protocols fixes them. Conditions it leaves open, such as
    65 °C or 85 °C, are its options; they stay empty here and are described in the
    notes. A test chooses among them in an `AppliedStandard`.

    The timeline shows its conditions, one row per variable, coloured by how it is
    fixed.
    """

    name = Quantity(
        type=str,
        description='The name of the standard as it writes it, e.g. `ISOS-L-2`.',
        a_eln=eln(ELNComponentEnum.StringEditQuantity),
    )
    reference = Quantity(
        type=URL,
        description='The publication of the standard, e.g. as a DOI link.',
        a_eln=eln(ELNComponentEnum.URLEditQuantity),
    )
    notes = Quantity(
        type=str,
        description="""
        How the standard's text was read: quotes, the options the standard leaves
        open, and what it does not state.
        """,
        a_eln=eln(ELNComponentEnum.RichTextEditQuantity),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Names the entry after the standard, makes the standard's name one of the
        methods by which NOMAD's apps find entries, and draws the timeline."""
        super().normalize(archive, logger)

        self.name = self.name.strip() if self.name else None
        self.figures = timeline_figures(self.name or '', [self])
        if self.name is None:
            return

        if archive.metadata is not None:
            archive.metadata.entry_name = self.name
        if archive.results is not None:
            if archive.results.eln is None:
                archive.results.eln = ELN()
            archive.results.eln.methods = [self.name]


class AppliedStandard(PlotSection, Conditions):
    """
    A standard as a test applies it: the standard, the choices this test made among
    its options, and conditions the standard leaves unstated, e.g. the interval of the
    J–V scans. The full conditions are the standard's together with these, and the
    timeline shows them together.
    """

    name = Quantity(
        type=str,
        description="""
        The name of the standard, e.g. `ISOS-L-2`: as written where the standard is
        named, or else that of the referenced standard.
        """,
        a_eln=eln(ELNComponentEnum.StringEditQuantity),
    )
    standard = Quantity(
        type=StabilityStandard,
        description='The standard that is applied.',
        a_eln=eln(ELNComponentEnum.ReferenceEditQuantity),
    )
    variant = Quantity(
        type=str,
        description="""
        The choices made among the standard's options, separated by commas, e.g.
        `85 °C, MPP`. Empty where the standard offers none.
        """,
        a_eln=eln(ELNComponentEnum.StringEditQuantity),
    )
    notes = Quantity(
        type=str,
        description='How the standard was applied, and where the test departs from it.',
        a_eln=eln(ELNComponentEnum.RichTextEditQuantity),
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Takes the name from the referenced standard where none is given, and draws
        the timeline of the standard's conditions together with these."""
        super().normalize(archive, logger)

        standard = self._referenced_standard(logger)
        self.name = self.name.strip() if self.name else None
        if self.name is None and standard is not None:
            self.name = standard.name
        title = f'{self.name} ({self.variant})' if self.variant else self.name
        conditions = [self] if standard is None else [standard, self]
        self.figures = timeline_figures(title or '', conditions)

    def _referenced_standard(self, logger: 'BoundLogger') -> 'StabilityStandard | None':
        """The referenced standard, or `None` where there is none or it cannot be
        read, e.g. because it is in an upload that is not visible."""
        standard = self.standard
        if not isinstance(standard, MProxy):
            return standard
        try:
            return standard.m_proxy_resolve()
        except Exception as error:
            logger.warning('could not read the applied standard', exc_info=error)
            return None


m_package.__init_metainfo__()
