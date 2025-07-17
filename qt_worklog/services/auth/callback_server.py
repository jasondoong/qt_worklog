import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import QObject, Signal


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

    def __init__(self, port=8080):
        super().__init__()
        self.port = port
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
