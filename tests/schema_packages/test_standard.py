from nomad import utils
from nomad.datamodel import EntryArchive, EntryMetadata

from nomad_pv_stability_standards.schema_packages.standard import (
    AppliedStandard,
    Atmosphere,
    Irradiance,
    OptoElectrical,
    RelativeHumidity,
    StabilityStandard,
    Temperature,
    Thermal,
)


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


#: The rows' names stand on their side, left of the rows.
ROW_NAME_ANGLE = -90


def row_names(section) -> list[str]:
    """The names of the timeline's rows, top to bottom, without their units."""
    layout = section.figures[0].figure['layout']
    return [
        note['text'].split('<br>')[0]
        for note in layout['annotations']
        if note.get('textangle') == ROW_NAME_ANGLE
    ]


def l2_light() -> StabilityStandard:
    return StabilityStandard(
        name='ISOS-L-2',
        opto_electrical_channel=[
            OptoElectrical(
                light='solar_simulator',
                irradiance=Irradiance(control='controlled', minimum=800, maximum=1000),
            )
        ],
    )


def test_the_timeline_has_one_row_per_stated_variable():
    standard = l2_light()
    standard.atmosphere_channel = [
        Atmosphere(gas='air', relative_humidity=RelativeHumidity(control='ambient'))
    ]
    archive = EntryArchive(metadata=EntryMetadata(), data=standard)
    standard.normalize(archive, utils.get_logger(__name__))

    assert row_names(standard) == ['irradiance', 'relative humidity']


def test_a_standard_without_conditions_has_no_timeline():
    assert normalized(name='ISOS-L-2').data.figures == []


def test_an_applied_standard_draws_the_standard_and_its_choices():
    applied = AppliedStandard(
        standard=l2_light(),
        variant='85 °C',
        thermal_channel=[
            Thermal(temperature=Temperature(control='controlled', minimum=358.15))
        ],
    )
    applied.normalize(EntryArchive(), utils.get_logger(__name__))

    assert applied.name == 'ISOS-L-2'
    assert row_names(applied) == ['irradiance', 'temperature']
    assert 'ISOS-L-2 (85 °C)' in applied.figures[0].figure['layout']['title']['text']


def test_the_gas_temperature_has_its_own_row_beside_the_device_temperature():
    standard = StabilityStandard(
        name='Damp heat under light',
        thermal_channel=[Thermal(temperature=Temperature(control='controlled'))],
        atmosphere_channel=[
            Atmosphere(
                temperature=Temperature(control='controlled', minimum=358.15),
                relative_humidity=RelativeHumidity(control='controlled', minimum=0.85),
            )
        ],
    )
    standard.normalize(
        EntryArchive(metadata=EntryMetadata()), utils.get_logger(__name__)
    )

    assert row_names(standard) == [
        'temperature',
        'gas temperature',
        'relative humidity',
    ]
