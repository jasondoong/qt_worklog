import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import QObject, Signal

from ... import config


def get_redirect_port():
    redirect_uri = config.GOOGLE_OAUTH_CLIENT_CONFIG["installed"]["redirect_uris"][0]
    parsed_uri = urlparse(redirect_uri)
    port = parsed_uri.port
    if port is None:
        if parsed_uri.scheme == "https":
            return 443
        return 80
    return port


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
