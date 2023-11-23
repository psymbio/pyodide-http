from io import BytesIO, IOBase
from ._core import Request, send
from ._core import _StreamingError, _StreamingTimeout

# in requests we override BaseAdapter instead of HTTPAdpater
from httpx._transports.base import BaseTransport
from httpx import Request, Response

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
        pass

