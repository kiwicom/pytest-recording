from itertools import chain
from typing import Any, Iterable, Iterator


def unique(sequence: Iterable) -> Iterator:
    seen = set()
    for item in sequence:
        if item not in seen:
            seen.add(item)
            yield item


def unpack(*args: Any) -> Iterable:
    return chain.from_iterable(args)
