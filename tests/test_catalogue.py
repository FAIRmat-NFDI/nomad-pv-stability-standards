from collections import Counter
from pathlib import Path

import pytest
import yaml
from nomad.client import normalize_all, parse

from nomad_pv_stability_standards.catalogue import build

PLUGIN = Path(__file__).parents[1]
SOURCES = PLUGIN / 'catalogue' / 'isos'
SHIPPED = PLUGIN / 'src' / 'nomad_pv_stability_standards' / 'example_uploads' / 'isos'


def shipped() -> dict[str, dict]:
    return {
        path.relative_to(SHIPPED).as_posix(): yaml.safe_load(
            path.read_text(encoding='utf-8')
        )['data']
        for path in sorted(SHIPPED.rglob('*.archive.yaml'))
    }


def test_the_shipped_files_are_built_from_the_sources():
    built = {name: archive['data'] for name, archive in build(SOURCES).items()}

    assert built == shipped()


def test_every_shipped_file_is_an_entry_named_after_standard_and_variant():
    for path in sorted(SHIPPED.rglob('*.archive.yaml')):
        archive = parse(str(path))[0]
        normalize_all(archive)
        data = archive.data
        name = f'{data.name} ({data.variant})' if data.variant else data.name

        assert archive.metadata.entry_name == name, path.name


def test_the_variants_are_the_combinations_of_the_options_of_each_protocol():
    """Table 1 and p. 37–39: temperatures, loads, biases, light–dark cycles and J–V
    light sources; ISOS-LC-3 has both humidity readings, ISOS-I has none."""
    variants = Counter(data['name'] for data in shipped().values() if 'variant' in data)
    temperatures, loads, biases, cycles = 2, 3, 5, 6

    assert variants == {
        'ISOS-D-1': 2,
        'ISOS-D-2': temperatures,
        'ISOS-D-3': temperatures,
        'ISOS-V-1': biases,
        'ISOS-V-2': temperatures * biases,
        'ISOS-V-3': temperatures * biases,
        'ISOS-L-1': loads,
        'ISOS-L-2': temperatures * loads,
        'ISOS-L-3': temperatures,
        'ISOS-O-1': loads,
        'ISOS-O-2': loads,
        'ISOS-T-1': temperatures,
        'ISOS-T-2': temperatures,
        'ISOS-LC-1': loads * cycles,
        'ISOS-LC-2': temperatures * loads * cycles,
        'ISOS-LC-3': temperatures * 2 * cycles,
        'ISOS-LT-1': 2 * loads,
        'ISOS-LT-2': loads,
        'ISOS-D-1I': 2,
        'ISOS-D-2I': temperatures,
        'ISOS-V-1I': biases,
        'ISOS-V-2I': temperatures * biases,
        'ISOS-L-1I': loads,
        'ISOS-L-2I': temperatures * loads,
        'ISOS-T-1I': temperatures,
        'ISOS-T-2I': temperatures,
        'ISOS-LC-1I': loads * cycles,
        'ISOS-LC-2I': temperatures * loads * cycles,
        'ISOS-LC-3I': temperatures * cycles,
    }


def test_every_protocol_has_one_entry_without_variant():
    names = [data['name'] for data in shipped().values()]
    without_variant = Counter(
        data['name'] for data in shipped().values() if 'variant' not in data
    )

    assert without_variant == Counter(set(names))


@pytest.mark.parametrize(
    'inert, based_on',
    [
        ('ISOS-L-2I (85 °C, MPP)', 'ISOS-L-2 (85 °C, MPP)'),
        ('ISOS-T-3I', 'ISOS-T-3'),
        ('ISOS-LC-3I (65 °C, 2 h, 1:1)', 'ISOS-LC-3 (65 °C, RH 50 %, 2 h, 1:1)'),
    ],
)
def test_an_inert_protocol_keeps_all_but_the_atmosphere(inert, based_on):
    """ "With the other parameters kept the same" (p. 42)."""
    by_name = {
        f'{data["name"]} ({data["variant"]})' if 'variant' in data else data['name']: (
            data
        )
        for data in shipped().values()
    }
    derived, original = by_name[inert], by_name[based_on]

    assert derived.get('thermal_channel') == original.get('thermal_channel')
    assert derived['opto_electrical_channel'] == original['opto_electrical_channel']
    assert [a['gas'] for a in derived['atmosphere_channel']] == ['inert, e.g. N2 or Ar']
