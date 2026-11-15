from collections.abc import Iterable, Iterator
from copy import deepcopy
from itertools import chain
from typing import Any, TypeVar

from _pytest.mark.structures import Mark

ConfigType = dict[str, Any]
T = TypeVar("T")


def unique(sequence: Iterable[T]) -> Iterator[T]:
    seen: set[T] = set()
    for item in sequence:
        if item not in seen:
            seen.add(item)
            yield item


def unpack(*args: Any) -> Iterable[Any]:
    return chain.from_iterable(args)


def merge_kwargs(config: ConfigType, markers: list[Mark]) -> ConfigType:
    """Merge all kwargs into a single dictionary to pass to `vcr.use_cassette`."""
    kwargs = deepcopy(config)
    for marker in reversed(markers):
        kwargs.update(marker.kwargs)
    return kwargs
