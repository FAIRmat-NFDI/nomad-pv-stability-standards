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


def test_the_entry_is_named_after_the_standard():
    assert normalized(name=' ISOS-L-2 ').metadata.entry_name == 'ISOS-L-2'


def test_the_standard_is_searchable_as_a_method():
    assert normalized(name='ISOS-L-2').results.eln.methods == ['ISOS-L-2']


def test_an_entry_without_name_keeps_the_name_of_its_file():
    archive = normalized(notes='A standard still to be named.')

    assert archive.metadata.entry_name == 'standard.archive.json'
