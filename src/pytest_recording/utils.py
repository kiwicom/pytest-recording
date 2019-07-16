from itertools import chain


def unique(sequence):
    seen = set()
    for item in sequence:
        if item not in seen:
            seen.add(item)
            yield item


def unpack(*args):
    return chain.from_iterable(args)
