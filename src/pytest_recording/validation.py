from _pytest.mark import Mark

from .exceptions import UsageError

ALLOWED_BLOCK_NETWORK_ARGUMENTS = ["allowed_hosts", "allow_private_ips"]


def validate_block_network_mark(mark: Mark) -> None:
    """Validate the input arguments for the `block_network` pytest mark."""
    if mark.args or not set(mark.kwargs) <= set(ALLOWED_BLOCK_NETWORK_ARGUMENTS):
        allowed_arguments = ", ".join("`{}`".format(arg) for arg in ALLOWED_BLOCK_NETWORK_ARGUMENTS)
        raise UsageError(
            "Invalid arguments to `block_network`. "
            "It accepts only the following keyword arguments: {}. "
            "Got args: {!r}; kwargs: {!r}".format(allowed_arguments, mark.args, mark.kwargs)
        )
