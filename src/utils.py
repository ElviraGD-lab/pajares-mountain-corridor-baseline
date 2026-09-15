"""Reusable functions for the Pajares baseline.

Function definitions only. No executable statements at module level, no calls,
no prints. The check is mechanical: every line must start with `def`, `import`,
`from`, a docstring, or a comment.

This rule exists because a stray call saved into a utility module fails far from
its cause -- typically as an ImportError in the first cell of an unrelated
notebook.
"""

import numpy as np
import pandas as pd


def reject_outliers(series, max_step):
    """Remove points that depart from both neighbours in the same direction.

    A closed deciduous canopy cannot gain or lose a large fraction of its NDVI
    between observations days apart. Such a point is residual cloud, shadow or
    haze that the quality mask missed.

    Applied before smoothing: a filter does not remove an error, it spreads the
    error across the neighbours and makes it invisible.

    Parameters
    ----------
    series : xarray.DataArray
        One-dimensional series indexed by time.
    max_step : float
        Maximum plausible change between consecutive observations.

    Returns
    -------
    xarray.DataArray
        Copy of the input with rejected points set to NaN.
    """
    values = series.values.copy()
    for i in range(1, len(values) - 1):
        prev_v, this_v, next_v = values[i - 1], values[i], values[i + 1]
        if np.isnan([prev_v, this_v, next_v]).any():
            continue
        if (abs(this_v - prev_v) > max_step
                and abs(this_v - next_v) > max_step
                and np.sign(this_v - prev_v) == np.sign(this_v - next_v)):
            values[i] = np.nan
    return series.copy(data=values)


def check_value_range(array, name, expected_min, expected_max):
    """Print the range of an array and flag values outside expectation.

    Numbers are inspected before images, always. A contrast stretch fitted to
    the data renders a corrupted array as a plausible landscape.
    """
    actual_min = float(array.min())
    actual_max = float(array.max())
    status = 'OK'
    if actual_min < expected_min or actual_max > expected_max:
        status = 'OUT OF RANGE'
    print(f'{name}: min={actual_min:.4f} max={actual_max:.4f}  [{status}]')
    return actual_min, actual_max