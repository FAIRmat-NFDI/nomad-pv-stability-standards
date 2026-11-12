from pathlib import Path

import pytest
import yaml
from nomad.client import normalize_all, parse

PLUGIN = Path(__file__).parents[1]
SHIPPED = PLUGIN / 'src' / 'nomad_pv_stability_standards' / 'example_uploads' / 'isos'


def shipped() -> dict[str, dict]:
    return {
        path.relative_to(SHIPPED).as_posix(): yaml.safe_load(
            path.read_text(encoding='utf-8')
        )['data']
        for path in sorted(SHIPPED.rglob('*.archive.yaml'))
    }


def by_name() -> dict[str, dict]:
    return {data['name']: data for data in shipped().values()}


def test_every_shipped_file_is_an_entry_named_after_its_standard():
    for path in sorted(SHIPPED.rglob('*.archive.yaml')):
        archive = parse(str(path))[0]
        normalize_all(archive)

        assert archive.metadata.entry_name == archive.data.name, path.name


def test_every_protocol_is_one_entry():
    """Table 1: 7 families at 3 levels; Table 2: 12 protocols in an inert atmosphere."""
    names = [data['name'] for data in shipped().values()]
    protocols = 7 * 3 + 12

    assert len(names) == len(set(names)) == protocols


@pytest.mark.parametrize(
    'inert, based_on',
    [('ISOS-L-2I', 'ISOS-L-2'), ('ISOS-T-3I', 'ISOS-T-3'), ('ISOS-LC-3I', 'ISOS-LC-3')],
)
def test_an_inert_protocol_keeps_all_but_the_atmosphere(inert, based_on):
    """ "With the other parameters kept the same" (p. 42)."""
    derived, original = by_name()[inert], by_name()[based_on]

    for channel in ('thermal_channel', 'opto_electrical_channel'):
        assert derived.get(channel) == original.get(channel)
    assert [atmosphere['gas'] for atmosphere in derived['atmosphere_channel']] == [
        'inert, e.g. N2 or Ar'
    ]


def test_only_isos_lc_3_is_provisional():
    """The paper contradicts itself only about the humidity of ISOS-LC-3; ISOS-LC-3I
    is performed "in the absence of humidity" (p. 42)."""
    provisional = {
        name
        for name, data in by_name().items()
        if 'Provisional' in yaml.safe_dump(data)
    }

    assert provisional == {'ISOS-LC-3'}
