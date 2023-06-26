try:
    from vcr.cassette import CassetteNotFoundError
except ImportError:
    # Required until vcrpy minimum version is v5.0.0, avoid type checking to
    # skip no-redef
    class CassetteNotFoundError(ValueError):  # type: ignore
        pass


class UsageError(Exception):
    """Error in plugin usage."""

    __module__ = "builtins"


__all__ = ["UsageError", "CassetteNotFoundError"]
