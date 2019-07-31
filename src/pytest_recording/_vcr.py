from copy import deepcopy
from itertools import chain, starmap

import attr
from vcr import VCR
from vcr.persisters.filesystem import FilesystemPersister
from vcr.serialize import deserialize

from .utils import unique, unpack


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


def use_cassette(vcr_cassette_dir, record_mode, markers, config):
    """Create a VCR instance and return an appropriate context manager for the given cassette configuration."""
    merged_config = merge_kwargs(config, markers)
    path_transformer = get_path_transformer(merged_config)
    vcr = VCR(path_transformer=path_transformer, cassette_library_dir=vcr_cassette_dir, record_mode=record_mode)
    # flatten the paths
    extra_paths = chain(*(marker[0] for marker in markers))
    persister = CombinedPersister(extra_paths)
    vcr.register_persister(persister)
    return vcr.use_cassette(markers[0][0][0], **merged_config)


def get_path_transformer(config):
    if "serializer" in config:
        suffix = ".{}".format(config["serializer"])
    else:
        suffix = ".yaml"
    return VCR.ensure_suffix(suffix)


def merge_kwargs(config, markers):
    """Merge all kwargs into a single dictionary to pass to `vcr.use_cassette`."""
    kwargs = deepcopy(config)
    for _, marker in reversed(markers):
        if marker is not None:
            kwargs.update(marker.kwargs)
    return kwargs
