"""
Builds the catalogue of standards: one archive file per standard and per variant, from
one source file per standard.

A source file holds the entry of the standard without options, and option groups. The
catalogue mirrors the folders of the source files, with one more folder per standard.

```yaml
name: ISOS-L-2
reference: https://doi.org/10.1038/s41560-019-0529-5
notes: Light soaking under a solar simulator.
thermal_channel: []         # conditions every variant shares
atmosphere_channel: []
opto_electrical_channel: []
options:                    # every combination of alternatives is one variant
  - notes: About this choice, written into every entry of the standard.
    alternatives:
      - label: 65 °C        # names the variant
        thermal_channel: [...]  # conditions added by this alternative
      - label: 85 °C
        thermal_channel: [...]
```

The entry without a variant holds only the shared conditions and lists the options in
its notes. A number with a unit is written as text, e.g. `65 °C` or `800 W/m^2`.

An `inert.yaml` file derives the protocols in an inert atmosphere, in its own folder: for
each standard in `based_on`, an entry named with a trailing `I` whose atmosphere is
replaced and whose options that change only the atmosphere are dropped.

Run `python -m nomad_pv_stability_standards.catalogue <sources> <output>` to rebuild.
"""

import itertools
import re
import sys
from pathlib import Path

import yaml
from nomad.units import ureg

from nomad_pv_stability_standards.schema_packages.standard import StabilityStandard

CONDITIONS = ('thermal_channel', 'atmosphere_channel', 'opto_electrical_channel')


def _value(quantity, value):
    if isinstance(value, str) and quantity.unit is not None:
        number, unit = value.split(' ', 1)
        return ureg.Quantity(float(number), unit)
    return value


def _section(section_def, values: dict):
    section = section_def.section_cls()
    for key, value in values.items():
        sub_section = section_def.all_sub_sections.get(key)
        if sub_section is None:
            quantity = section_def.all_quantities[key]
            setattr(section, key, _value(quantity, value))
            continue
        for item in value if sub_section.repeats else [value]:
            section.m_add_sub_section(
                sub_section, _section(sub_section.sub_section, item)
            )
    return section


def _join_notes(*notes) -> str | None:
    return '\n\n'.join(note.strip() for note in notes if note) or None


def _entry(source: dict, choice: tuple[dict, ...]) -> dict:
    """The values of the entry that takes one alternative of each option group, or of
    the entry without a variant for an empty `choice`."""
    groups = source.get('options', [])
    entry = {
        'name': source['name'],
        'reference': source.get('reference'),
        'notes': _join_notes(
            source.get('notes'),
            *(group.get('notes') for group in groups),
            *(alternative.get('notes') for alternative in choice),
        ),
    }
    if choice:
        entry['variant'] = ', '.join(alternative['label'] for alternative in choice)
    elif groups:
        options = '; '.join(
            ' or '.join(alternative['label'] for alternative in group['alternatives'])
            for group in groups
        )
        entry['notes'] = _join_notes(
            entry['notes'], f'Options, one variant per combination: {options}.'
        )
    for condition in CONDITIONS:
        entry[condition] = list(source.get(condition, [])) + [
            item for alternative in choice for item in alternative.get(condition, [])
        ]
    return {key: value for key, value in entry.items() if value}


def entries(source: dict) -> list[dict]:
    """The entry without a variant and one entry per combination of alternatives."""
    groups = [group['alternatives'] for group in source.get('options', [])]
    choices = list(itertools.product(*groups)) if groups else []
    return [_entry(source, ())] + [_entry(source, choice) for choice in choices]


def inert(source: dict, rule: dict) -> dict:
    """The source of the protocol in an inert atmosphere based on `source`."""
    return {
        **source,
        'name': f'{source["name"]}I',
        'notes': _join_notes(source.get('notes'), rule.get('notes')),
        'atmosphere_channel': rule['atmosphere_channel'],
        'options': [
            group
            for group in source.get('options', [])
            if any(
                set(alternative) - {'label', 'notes', 'atmosphere_channel'}
                for alternative in group['alternatives']
            )
        ],
    }


def file_name(entry: dict) -> str:
    """A file name made of the entry's name and variant, e.g.
    `ISOS-LC-2_85C_MPP_24h_1-2.archive.yaml`."""
    words = [entry['name'], *entry.get('variant', '').split(',')]
    replace = {'°': '', '%': 'pct', '<': 'below', '−': '-', ':': '-', ' ': ''}
    slugs = []
    for word in words:
        slug = word
        for old, new in replace.items():
            slug = slug.replace(old, new)
        if slug:
            slugs.append(re.sub(r'[^A-Za-z0-9_.-]', '', slug))
    return '_'.join(slugs) + '.archive.yaml'


def build(sources: Path) -> dict[str, dict]:
    """The archive of every entry, by its path in the catalogue, from the source files
    in `sources`. The entries of a standard are in a folder named after it, inside the
    folder of its source file, e.g. `ISOS-L/ISOS-L-2/ISOS-L-2_65C_MPP.archive.yaml`."""
    standards, folders = {}, {}
    for path in sorted(sources.rglob('*.yaml')):
        if path.name == 'inert.yaml':
            continue
        source = yaml.safe_load(path.read_text(encoding='utf-8'))
        standards[source['name']] = source
        folders[source['name']] = path.parent.relative_to(sources)
    for inert_path in sorted(sources.rglob('inert.yaml')):
        rule = yaml.safe_load(inert_path.read_text(encoding='utf-8'))
        for name in rule['based_on']:
            derived = inert(standards[name], rule)
            standards[derived['name']] = derived
            folders[derived['name']] = inert_path.parent.relative_to(sources)

    archives = {}
    for name, source in standards.items():
        for entry in entries(source):
            data = _section(StabilityStandard.m_def, entry)
            path = (folders[name] / name / file_name(entry)).as_posix()
            archives[path] = {'data': data.m_to_dict(with_root_def=True)}
    return archives


def write(sources: Path, output: Path) -> None:
    """Replaces the archive files in `output` by those built from `sources`."""
    for old in output.rglob('*.archive.yaml'):
        old.unlink()
    for folder in sorted(output.rglob('*'), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    for path, archive in build(sources).items():
        target = output / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            yaml.safe_dump(archive, allow_unicode=True, sort_keys=False),
            encoding='utf-8',
        )


if __name__ == '__main__':
    write(Path(sys.argv[1]), Path(sys.argv[2]))
