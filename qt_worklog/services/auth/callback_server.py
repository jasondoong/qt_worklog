import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import QObject, Signal

from ... import config


def _port_from_config() -> int | None:
    """Return port explicitly specified in redirect_uris if present."""
    redirect_uris = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"].get(
        "redirect_uris", []
    )
    for uri in redirect_uris:
        parsed = urlparse(uri)
        if (
            parsed.scheme == "http"
            and parsed.hostname == "localhost"
            and parsed.port
        ):
            return parsed.port
    return None


def _find_free_port() -> int:
    """Ask the OS for an available high port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def get_redirect_port() -> int:
    """Determine which port the local OAuth callback server should bind."""
    port = _port_from_config()
    if port:
        return port
    try:
        return _find_free_port()
    except OSError:
        # Final fallback to common ports if everything else fails
        for fallback in (8080, 8888):
            try:
                with socket.socket() as s:
                    s.bind(("", fallback))
                return fallback
            except OSError:
                continue
        raise RuntimeError("Unable to determine a free port for OAuth callback")


class CallbackHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.callback_server = kwargs.pop("callback_server")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        query_components = parse_qs(urlparse(self.path).query)
        code = query_components.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Authentication successful!</h1><p>You can close this window now.</p>")

        if code:
            self.callback_server.authorization_code_received.emit(code)


class CallbackServer(QObject):
    authorization_code_received = Signal(str)

    def __init__(self):
        super().__init__()
        self.port = get_redirect_port()
        self.server = None
        self.thread = None

    def start(self):
        handler = lambda *args, **kwargs: CallbackHandler(*args, callback_server=self, **kwargs)
        self.server = HTTPServer(("", self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
