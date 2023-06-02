import os
from copy import deepcopy
from itertools import chain, starmap
from types import ModuleType
from typing import Any, Callable, Dict, List, Tuple

import attr
from _pytest.config import Config
from _pytest.mark.structures import Mark
from vcr import VCR
from vcr.cassette import CassetteContextDecorator
from vcr.persisters.filesystem import FilesystemPersister
from vcr.serialize import deserialize

from .utils import unique, unpack

ConfigType = Dict[str, Any]


def load_cassette(cassette_path: str, serializer: ModuleType) -> Tuple[List, List]:
    try:
        with open(cassette_path, encoding="utf8") as f:
            cassette_content = f.read()
    except OSError:
        return [], []
    return deserialize(cassette_content, serializer)


@attr.s(slots=True)
class CombinedPersister(FilesystemPersister):
    """Load extra cassettes, but saves only the first one."""

    extra_paths = attr.ib(type=List[str])

    # FilesystemPersister.load_casette is a classmethod, which
    # is likely why pylint gives an error.
    def load_cassette(  # pylint: disable=arguments-differ
        self, cassette_path: str, serializer: ModuleType
    ) -> Tuple[List, List]:
        all_paths = chain.from_iterable(((cassette_path,), self.extra_paths))
        # Pairs of 2 lists per cassettes:
        all_content = (load_cassette(path, serializer) for path in unique(all_paths))
        # Two iterators from all pairs from above: all requests, all responses
        # Notes.
        # 1. It is possible to do it with accumulators, for loops and `extend` calls,
        #    but the functional approach is faster
        # 2. It could be done more efficient, but the `deserialize` implementation should be adjusted as well
        #    But it is a private API, which could be changed.
        requests, responses = starmap(unpack, zip(*all_content))
        requests, responses = list(requests), list(responses)
        if not requests or not responses:
            raise ValueError("No cassettes found.")
        return requests, responses


# pylint: disable=too-many-arguments
def use_cassette(
    default_cassette: str,
    vcr_cassette_dir: str,
    record_mode: str,
    markers: List[Mark],
    config: ConfigType,
    pytestconfig: Config,
) -> CassetteContextDecorator:
    """Create a VCR instance and return an appropriate context manager for the given cassette configuration."""
    merged_config = merge_kwargs(config, markers)
    if "record_mode" in merged_config:
        record_mode = merged_config["record_mode"]
    path_transformer = get_path_transformer(merged_config)
    if record_mode == "rewrite":
        path = path_transformer(os.path.join(vcr_cassette_dir, default_cassette))
        try:
            os.remove(path)
        except OSError:
            pass
        record_mode = "new_episodes"
    vcr = VCR(path_transformer=path_transformer, cassette_library_dir=vcr_cassette_dir, record_mode=record_mode)

    def extra_path_transformer(path: str) -> str:
        """Paths in extras can be handled as relative and as absolute.

        Relative paths will be checked in `vcr_cassette_dir`.
        """
        if not os.path.isabs(path):
            return os.path.join(vcr_cassette_dir, path)
        return path

    extra_paths = [extra_path_transformer(path) for marker in markers for path in marker.args]
    persister = CombinedPersister(extra_paths)
    vcr.register_persister(persister)
    pytestconfig.hook.pytest_recording_configure(config=pytestconfig, vcr=vcr)
    return vcr.use_cassette(default_cassette, **merged_config)


def get_path_transformer(config: ConfigType) -> Callable:
    if "serializer" in config:
        suffix = ".{}".format(config["serializer"])
    else:
        suffix = ".yaml"
    return VCR.ensure_suffix(suffix)


def merge_kwargs(config: ConfigType, markers: List[Mark]) -> ConfigType:
    """Merge all kwargs into a single dictionary to pass to `vcr.use_cassette`."""
    kwargs = deepcopy(config)
    for marker in reversed(markers):
        kwargs.update(marker.kwargs)
    return kwargs
