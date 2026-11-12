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

from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.results import ELN
from nomad.metainfo import Quantity, SchemaPackage

m_package = SchemaPackage()


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
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    variant = Quantity(
        type=str,
        description="""
        The options of the standard that this entry takes, separated by commas, e.g.
        `65 °C, MPP`. Empty where the entry takes no option.
        """,
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )
    reference = Quantity(
        type=str,
        description='The publication of the standard, e.g. as a DOI link.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.URLEditQuantity),
    )
    notes = Quantity(
        type=str,
        description="""
        How the standard's text was read: quotes, options the standard leaves open,
        and what it does not state.
        """,
        a_eln=ELNAnnotation(component=ELNComponentEnum.RichTextEditQuantity),
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
