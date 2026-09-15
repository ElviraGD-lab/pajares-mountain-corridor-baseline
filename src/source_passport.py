"""Write a source passport next to downloaded data.

A source passport records where a dataset came from, under what licence, when it
was retrieved and which assumptions apply to it. It is written at download time,
in the same folder as the data, because that is the only place it will still be
found in six months.

Works unchanged in Colab and locally: the caller supplies the folder.

Usage
-----
    from source_passport import write_passport

    write_passport(
        folder=data_folder,
        title='Administrative boundaries - Asturias',
        url=adm3_url,
        licence='ODbL - attribution required, derived work under same licence',
        attribution='FieldMaps / geoBoundaries, ODbL',
        crs='EPSG:4326 as delivered',
        files={
            'asturias_concejos.gpkg': 'all 78 concejos of Asturias',
            'study_sites_concejos.gpkg': 'Cabrales and Lena only',
        },
        version='ADM3, edge-matched open',
        notes=[
            'adm3 in Spain = municipio; in Asturias these are named "concejos".',
            'Pajares is a village inside the concejo of Lena, not a concejo itself.',
            'Boundaries differ from IGN and catastro by tens of metres.',
            'Areas computed in EPSG:25830 (ETRS89 / UTM 30N).',
        ],
    )
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone


def write_passport(
    folder: str,
    title: str,
    url: str,
    licence: str,
    files: dict[str, str],
    attribution: str | None = None,
    crs: str | None = None,
    version: str | None = None,
    notes: list[str] | None = None,
    filename: str = 'README.md',
) -> str:
    """Write a passport file and return its path.

    Parameters
    ----------
    folder
        Directory holding the data. Created if missing.
    title
        Short description of the dataset.
    url
        Where the data was retrieved from.
    licence
        Licence text or name, including conditions that affect reuse.
    files
        Mapping of filename to a one-line description of its contents.
    attribution
        Exact wording required by the licence, if any.
    crs
        Coordinate reference system as delivered.
    version
        Release identifier or coverage number. Pin it: "latest" is not
        reproducible.
    notes
        Assumptions and caveats specific to this dataset.
    filename
        Name of the passport file.
    """
    os.makedirs(folder, exist_ok=True)

    lines = [
        f'# {title}',
        '',
        f'- **Source URL:** {url}',
        f'- **Licence:** {licence}',
    ]
    if attribution:
        lines.append(f'- **Required attribution:** {attribution}')
    if version:
        lines.append(f'- **Version / release:** {version}')
    if crs:
        lines.append(f'- **CRS:** {crs}')
    lines.append(f'- **Retrieved:** {date.today().isoformat()}')
    lines.append(f'- **Passport written:** '
                 f'{datetime.now(timezone.utc).isoformat(timespec="seconds")}')

    lines += ['', '## Files', '']
    for name, description in files.items():
        lines.append(f'- `{name}` - {description}')

    if notes:
        lines += ['', '## Notes and assumptions', '']
        for note in notes:
            lines.append(f'- {note}')

    lines += [
        '',
        '---',
        '',
        'Written automatically at download time by `src/source_passport.py`.',
        'Assumptions listed here must also appear in `docs/ASSUMPTIONS.md`.',
        '',
    ]

    path = os.path.join(folder, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return path