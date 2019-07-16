from itertools import chain, starmap

import attr
from vcr import VCR
from vcr.persisters.filesystem import FilesystemPersister
from vcr.serialize import deserialize

from .utils import unpack, unique


def load_cassette(cassette_path, serializer):
    try:
        with open(cassette_path) as f:
            cassette_content = f.read()
    except IOError:
        return [], []
    return deserialize(cassette_content, serializer)


@attr.s(slots=True)
class CombinedPersister(FilesystemPersister):
    """Load extra cassettes, but saves only the first one."""

    extra_paths = attr.ib()

    def load_cassette(self, cassette_path, serializer):
        all_paths = chain.from_iterable(((cassette_path,), self.extra_paths))
        # Pairs of 2 lists per cassettes:
        all_content = (load_cassette(path, serializer) for path in unique(all_paths))
        # Two iterators from all pairs from above: all requests, all responses
        # Notes.
        # 1. It is possible to do it with accumulators, for loops and `extend` calls,
        #    but the functional approach is faster
        # 2. It could be done more efficient, but the `deserialize` implementation should be adjusted as well
        #    But it is a private API, which could be changed.
        return starmap(unpack, zip(*all_content))


def make_cassette(vcr_cassette_dir, record_mode, markers):
    """Create a VCR instance and return an appropriate context manager for the given cassette configuration."""
    vcr = VCR(
        path_transformer=VCR.ensure_suffix(".yaml"), cassette_library_dir=vcr_cassette_dir, record_mode=record_mode
    )
    closest_marker_paths, _ = markers[0]
    extra_paths = get_extra_paths(closest_marker_paths[1:], markers[1:])
    persister = CombinedPersister(extra_paths)
    vcr.register_persister(persister)
    return vcr.use_cassette(closest_marker_paths[0], **merge_kwargs(markers))


def get_extra_paths(paths, markers):
    """All extra paths from the closest mark and all paths from the other applied marks."""
    return chain(paths, *(marker[0] for marker in markers if marker[0] is not None))


def merge_kwargs(markers):
    """Merge all kwargs into a single dictionary to pass to `vcr.use_cassette`."""
    kwargs = {}
    for _, marker in reversed(markers):
        if marker is not None:
            kwargs.update(marker.kwargs)
    return kwargs
