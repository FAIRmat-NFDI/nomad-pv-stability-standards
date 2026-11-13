"""The channels of a standard drawn as a timeline: one row per variable, coloured by how
it is fixed, over a few repetitions of whatever repeats."""

from math import ceil

import numpy as np
from nomad.datamodel.metainfo.plot import PlotlyFigure

from nomad_pv_stability_standards.schema_packages.plotting_series import (
    HOUR,
    ITERATIONS_FOR_PLOTTING,
    MONITORED,
    PlotPiece,
    TimePlotSeries,
    shown,
)
from nomad_pv_stability_standards.schema_packages.plotting_timeline import (
    figure_for_plotting,
)

#: The variables of each channel, and the row each is drawn on.
VARIABLES = {
    'thermal_channel': {'temperature': 'temperature'},
    'opto_electrical_channel': {
        'irradiance': 'irradiance',
        'voltage': 'electrical load',
        'current_density': 'electrical load',
    },
    'atmosphere_channel': {
        'temperature': 'gas temperature',
        'relative_humidity': 'relative humidity',
        'oxygen_fraction': 'oxygen fraction',
    },
}

#: The colour of a variable by its `control`: whatever is driven is `controlled`.
ROLES = {
    'controlled': 'controlled',
    'set': 'controlled',
    'tracked': 'controlled',
    'swept': 'controlled',
    'cycled': 'controlled',
    'specified': 'specified',
}

LIGHT = {'dark': 'dark', 'solar_simulator': 'solar simulator', 'sunlight': 'sunlight'}


def timeline_figures(title: str, conditions: list) -> list[PlotlyFigure]:
    """The timeline of the channels of all `conditions` together, e.g. a standard and
    what a test applies on top of it; none where there is nothing to draw."""
    items = [
        (channel, item)
        for section in conditions
        for channel in VARIABLES
        for item in getattr(section, channel, None) or []
    ]
    periods = [_seconds(item.period) for _, item in items if item.period is not None]
    end = max([ITERATIONS_FOR_PLOTTING * period for period in periods] + [HOUR])
    series = TimePlotSeries(end=end)
    for channel, item in items:
        series.pieces += _pieces(channel, item, end)
    if not series.pieces:
        return []
    figure = figure_for_plotting(series, title, continues=True)
    return [PlotlyFigure(label='Timeline', index=0, open=True, figure=figure)]


def _pieces(channel: str, item, end: float) -> list[PlotPiece]:
    """The pieces one condition draws: each of its variables on its row, during the
    condition's phases."""
    light = LIGHT.get(getattr(item, 'light', None) or '')
    variables = {
        name: variable
        for name in VARIABLES[channel]
        if (variable := getattr(item, name, None)) is not None
    }
    if any(variable.control == 'swept' for variable in variables.values()):
        return [_scan(item, light, end)]

    spans, endless = _spans(item, end)
    pieces = []
    if light and 'irradiance' not in variables and channel == 'opto_electrical_channel':
        pieces += _bars('irradiance', light, 'unspecified', spans, endless)
    for name, variable in variables.items():
        row = VARIABLES[channel][name]
        label = _described(variable)
        if name == 'irradiance' and light:
            label = ', '.join(filter(None, [light, label]))
        if label:
            pieces += _drawn(row, label, variable, spans, endless)
        if variable.monitored:
            pieces += _bars(row + MONITORED, 'monitored', 'monitored', spans, endless)
    return pieces


def _spans(item, end: float) -> tuple[list[tuple[float, float]], bool]:
    """When a condition acts: throughout, or in the active part of each period."""
    if item.period is None:
        return [(0.0, end)], True
    period = _seconds(item.period)
    active = (
        _seconds(item.active_duration) if item.active_duration is not None else None
    )
    return [
        (k * period, k * period + (active or period)) for k in range(ceil(end / period))
    ], False


def _scan(item, light: str | None, end: float) -> PlotPiece:
    """A J–V scan as marks at each repetition; one mark, and a note, where the
    standard states no interval."""
    label = f'J–V scan under {light}' if light else 'J–V scan'
    if item.period is None:
        return PlotPiece(
            row='electrical load',
            label=label,
            start=0.0,
            end=end,
            role='controlled',
            marks=np.array([0.0]),
            mark_kind='J–V scan',
            assumption='J–V interval not stated',
        )
    period = _seconds(item.period)
    return PlotPiece(
        row='electrical load',
        label=label,
        start=0.0,
        end=end,
        role='controlled',
        marks=np.arange(0.0, end + period / 2, period),
        mark_kind='J–V scan',
    )


def _drawn(row, label, variable, spans, endless) -> list[PlotPiece]:
    """A variable during each span: a line at a single value, a band between two, or
    a bar with its label where it has no numbers to draw."""
    role = ROLES.get(variable.control, 'unspecified')
    low, high = variable.minimum, variable.maximum
    pieces = []
    for start, stop in spans:
        piece = PlotPiece(
            row=row, label=label, start=start, end=stop, role=role, endless=endless
        )
        if low is not None and high is not None:
            if low == high and variable.control != 'cycled':
                piece.times = np.array([start, stop])
                piece.values = np.array([low.magnitude] * 2) * low.units
            else:
                piece.bounds = (low, high)
                piece.text = label
        else:
            piece.text = label
        pieces.append(piece)
    return pieces


def _bars(row, text, role, spans, endless) -> list[PlotPiece]:
    return [
        PlotPiece(
            row=row,
            label=text,
            start=start,
            end=stop,
            text=text,
            role=role,
            endless=endless,
        )
        for start, stop in spans
    ]


def _described(variable) -> str:
    """How a variable is fixed, e.g. `controlled, 65 °C`, `tracked: MPP` or
    `specified, below 50 %`."""
    control = variable.control or ''
    if variable.target:
        control = f'{control}: {variable.target}' if control else variable.target
    low, high = variable.minimum, variable.maximum
    if low is not None and high is not None:
        values = shown(low) if low == high else f'{shown(low)} to {shown(high)}'
    elif high is not None:
        values = f'below {shown(high)}'
    elif low is not None:
        values = f'from {shown(low)}'
    else:
        values = ''
    return ', '.join(filter(None, [control, values]))


def _seconds(duration) -> float:
    return duration.to('s').magnitude
