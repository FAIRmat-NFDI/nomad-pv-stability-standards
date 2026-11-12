import pytest
from nomad import utils
from nomad.datamodel import EntryArchive, EntryMetadata

from nomad_pv_stability_standards.schema_packages.standard import StabilityStandard


def normalized(**values) -> EntryArchive:
    """The archive of a `StabilityStandard` with `values`, normalized as NOMAD
    normalizes the entry of an archive file."""
    archive = EntryArchive(
        metadata=EntryMetadata(mainfile='standard.archive.json'),
        data=StabilityStandard(**values),
    )
    archive.data.normalize(archive, utils.get_logger(__name__))
    return archive


@pytest.mark.parametrize(
    'variant, entry_name',
    [
        (None, 'ISOS-L-2'),
        ('65 °C, MPP', 'ISOS-L-2 (65 °C, MPP)'),
        ('  65 °C, MPP ', 'ISOS-L-2 (65 °C, MPP)'),
    ],
)
def test_the_entry_is_named_after_standard_and_variant(variant, entry_name):
    assert normalized(name=' ISOS-L-2', variant=variant).metadata.entry_name == (
        entry_name
    )


def test_the_standard_is_searchable_as_a_method():
    archive = normalized(name='ISOS-L-2', variant='65 °C, MPP')

    assert archive.results.eln.methods == ['ISOS-L-2']


def test_an_entry_without_name_keeps_the_name_of_its_file():
    archive = normalized(variant='65 °C')

    assert archive.metadata.entry_name == 'standard.archive.json'
