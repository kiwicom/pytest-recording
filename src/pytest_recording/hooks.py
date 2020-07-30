from _pytest.config import Config
from vcr import VCR


def pytest_recording_configure(config: Config, vcr: VCR) -> None:
    pass  # pragma: no cover
