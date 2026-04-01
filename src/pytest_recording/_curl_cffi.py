"""VCR.py integration for curl_cffi.

Patches ``curl_cffi.requests.Session.request`` so that requests made via
curl_cffi are recorded into / replayed from VCR cassettes, just like
requests made through ``urllib3`` or ``httpx``.
"""

from contextlib import contextmanager
from typing import Any, Iterator

from vcr.errors import CannotOverwriteExistingCassetteException
from vcr.request import Request

try:
    import curl_cffi.requests
    from curl_cffi.requests import Response
    from curl_cffi.requests.headers import Headers

    _has_curl_cffi = True
except ImportError:
    _has_curl_cffi = False

_original_request = None


def _make_vcr_request(method: str, url: str, kwargs: dict) -> Request:
    headers = kwargs.get("headers") or {}
    body = kwargs.get("data") or kwargs.get("json")
    return Request(method=method.upper(), uri=str(url), body=body, headers=dict(headers))


def _make_vcr_response(response: Any) -> dict:
    headers = {k: [v] for k, v in response.headers.items()}
    return {
        "status": {"code": response.status_code, "message": response.reason or ""},
        "headers": headers,
        "body": {"string": response.content},
    }


def _play_response(vcr_response: dict) -> Any:
    response = Response()
    response.status_code = vcr_response["status"]["code"]
    response.reason = vcr_response["status"]["message"]
    body = vcr_response["body"]["string"]
    response.content = body.encode() if isinstance(body, str) else body
    header_items = []
    for key, values in vcr_response["headers"].items():
        for value in values:
            header_items.append((key, value))
    response.headers = Headers(header_items)
    return response


@contextmanager
def patch(cassette: Any) -> Iterator[None]:
    """Patch ``curl_cffi.requests.Session.request`` to use VCR cassette."""
    if not _has_curl_cffi:
        yield
        return

    global _original_request
    _original_request = curl_cffi.requests.Session.request

    def _patched_request(self: Any, method: str, url: str, **kwargs: Any) -> Any:
        vcr_request = _make_vcr_request(method, url, kwargs)

        if cassette.can_play_response_for(vcr_request):
            vcr_response = cassette.play_response(vcr_request)
            return _play_response(vcr_response)

        if cassette.write_protected and cassette.filter_request(vcr_request):
            raise CannotOverwriteExistingCassetteException(
                cassette=cassette,
                failed_request=vcr_request,
            )

        assert _original_request is not None
        response = _original_request(self, method, url, **kwargs)  # type: ignore[arg-type]
        cassette.append(vcr_request, _make_vcr_response(response))
        return response

    curl_cffi.requests.Session.request = _patched_request  # type: ignore[assignment]
    try:
        yield
    finally:
        curl_cffi.requests.Session.request = _original_request  # type: ignore[assignment]
        _original_request = None
