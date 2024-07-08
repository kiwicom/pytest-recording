from _pytest.config import Config
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vcr import VCR


def pytest_recording_configure(config: Config, vcr: "VCR") -> None:
    pass  # pragma: no cover
