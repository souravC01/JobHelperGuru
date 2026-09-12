import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARGET = "https://jobhelperguru.vercel.app"


class RedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()

    def do_HEAD(self):
        self.handle_request(head_only=True)

    def handle_request(self, head_only=False):
        if self.path.split("?", 1)[0] in ("/health", "/api/health"):
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()

            if not head_only:
                self.wfile.write(body)
            return

        self.send_response(302)
        self.send_header("Location", TARGET + self.path)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def log_message(self, format, *args):
        print(format % args)


port = int(os.environ.get("PORT", "10000"))

server = ThreadingHTTPServer(("0.0.0.0", port), RedirectHandler)

print(f"Legacy redirect listening on port {port}")
server.serve_forever()
