"""NumNy-related utility functions."""

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence
    from typing import Any, Optional


def dict2recarray(
    excel_dict: dict[str, "Any"], names: "Optional[Sequence[str]]" = None
) -> np.recarray:
    """Converts a dict returned by the Excel parser to a numpy rec array.

    If `names` is None, the record names are inferred from `excel_dict`.
    """
    arrays = []
    for arr in excel_dict.values():
        if all(
            isinstance(v, (bool, int, float, complex, None.__class__))
            for v in arr
        ):
            arrays.append([np.nan if v is None else v for v in arr])
        elif all(isinstance(v, (str, bytes, None.__class__)) for v in arr):
            arrays.append(["" if v is None else v for v in arr])
        else:
            arrays.append(arr)
        if names is None:
            names = list(excel_dict.keys())
    return np.rec.fromarrays(arrays, names=names)
