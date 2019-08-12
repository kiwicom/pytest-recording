try:
    from inspect import Signature

    get_signature = Signature.from_callable  # pylint: disable=unused-import
except ImportError:
    from funcsigs import signature as get_signature  # pylint: disable=unused-import


try:
    from collections.abc import Iterable  # pylint: disable=unused-import
except ImportError:
    # Python 2
    from collections import Iterable
