from .mutagens import status_code, malform_body, empty_body, reduce_body
from .core import mutation, MutationGroup


DEFAULT_STATUS_CODES = (400, 401, 403, 404, 500, 501, 502, 503)

DEFAULT = MutationGroup((status_code(code=DEFAULT_STATUS_CODES), empty_body, malform_body, reduce_body))

del MutationGroup  # Not needed in the API
