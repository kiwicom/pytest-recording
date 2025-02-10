from copy import deepcopy
from itertools import chain
from typing import Any, Dict, Iterable, Iterator, List

from _pytest.mark.structures import Mark

ConfigType = Dict[str, Any]


def unique(sequence: Iterable) -> Iterator:
    seen = set()
    for item in sequence:
        if item not in seen:
            seen.add(item)
            yield item


def unpack(*args: Any) -> Iterable:
    return chain.from_iterable(args)


def merge_kwargs(config: ConfigType, markers: List[Mark]) -> ConfigType:
    """Merge all kwargs into a single dictionary to pass to `vcr.use_cassette`."""
    kwargs = deepcopy(config)
    for marker in reversed(markers):
        kwargs.update(marker.kwargs)
    return kwargs
