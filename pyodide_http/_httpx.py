from io import BytesIO, IOBase
from ._core import Request, send
from ._core import _StreamingError, _StreamingTimeout

# in requests we override BaseAdapter instead of HTTPAdpater
from httpx._transports.base import BaseTransport
from httpx import Request, Response
from httpx._utils import obfuscate_sensitive_headers
from requests.utils import get_encoding_from_headers, CaseInsensitiveDict

from ._core import Request as PyodideRequest

class PyodideHTTPTransport(BaseTransport):
    # here we need to only implement handle_request function
    # as parent class has already implemented the rest
    def handle_request(self, request: Request) -> Response:
        """
        Send a single HTTP request and return a response.

        Developers shouldn't typically ever need to call into this API directly,
        since the Client class provides all the higher level user-facing API
        niceties.

        In order to properly release any network resources, the response
        stream should *either* be consumed immediately, with a call to
        `response.stream.read()`, or else the `handle_request` call should
        be followed with a try/finally block to ensuring the stream is
        always closed.

        Example usage:

            with httpx.HTTPTransport() as transport:
                req = httpx.Request(
                    method=b"GET",
                    url=(b"https", b"www.example.com", 443, b"/"),
                    headers=[(b"Host", b"www.example.com")],
                )
                resp = transport.handle_request(req)
                body = resp.stream.read()
                print(resp.status_code, resp.headers, body)


        Takes a `Request` instance as the only argument.

        Returns a `Response` instance.
        """
        # None handling for stream already done in httpx.Request
        stream = request.stream
        pyodide_request = PyodideRequest(request.method, request.url)

        # timeout is not present in httpx.Request class
        pyodide_request.timeout = 0

        if request.body:
            pyodide_request.set_body(request.body)
        try:
            resp = send(pyodide_request, stream)
        except _StreamingTimeout:
            from httpx import ConnectTimeout

            # should the passed argument here be the pyodide_request or request arg of the function
            # ConnectTimeout from httpx takes the Request class object from the httpx
            # otherwise on ._core we would need to define another Request class for Pyodide as timeout is not present in httpx.Request class
            raise ConnectTimeout(request=pyodide_request)
        except _StreamingError:
            from httpx import ConnectionError
            raise ConnectionError(request=pyodide_request)
        import httpx
        response = httpx.Response()
        # Fallback to None if there's no status_code, for whatever reason.
        response.status_code = getattr(resp, "status_code", None)
        # Make headers case-insensitive.
        response.headers = obfuscate_sensitive_headers(resp.headers)
        # response.headers = CaseInsensitiveDict(resp.headers)
        
        # Set encoding.
        response.default_encoding = "utf-8"
        if isinstance(resp.body, IOBase):
            # streaming response
            response.raw = resp.body
        else:
            # non-streaming response, make it look like a stream
            response.raw = BytesIO(resp.body)

        response.request = request
        return response

def patch():
    global _IS_PATCHED
    """
        Patch the requests Session. Will add a new adapter for the http and https protocols.

        Keep in mind the browser is stricter with things like CORS and this can cause some
        requests to fail that work with the regular Adapter.
    """
    if _IS_PATCHED:
        return

    import httpx
    httpx.AsyncClient._old_init = httpx.AsyncClient.__init__

    def new_init(self, *args, **kwargs):
        self._old_init(*args, **kwargs)
        self._client._transports[b"http"] = PyodideHTTPTransport()
        self._client._transports[b"https"] = PyodideHTTPTransport()

    httpx.AsyncClient.__init__ = new_init
    _IS_PATCHED = True
