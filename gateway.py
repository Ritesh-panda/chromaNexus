import os
import sys
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error

BACKEND_URL = "http://127.0.0.1:8000"
DIST_DIR = r"C:\chromaNexus\dist"
PORT = 3000

mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")

class FastReverseProxyAndStaticServer(BaseHTTPRequestHandler):
    def do_proxy_backend(self):
        target_url = f"{BACKEND_URL}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        req_headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ("host", "content-length", "accept-encoding"):
                req_headers[k] = v
        req_headers["Host"] = "127.0.0.1:8000"
        
        req = urllib.request.Request(target_url, data=body, headers=req_headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "content-encoding", "connection", "content-length"):
                        self.send_header(k, v)
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ("transfer-encoding", "content-encoding", "connection", "content-length"):
                    self.send_header(k, v)
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Proxy Gateway Error: {e}".encode())

    def do_serve_static(self):
        clean_path = self.path.split("?")[0].lstrip("/")
        if not clean_path:
            file_path = os.path.join(DIST_DIR, "index.html")
        else:
            potential_file = os.path.join(DIST_DIR, clean_path.replace("/", os.sep))
            if os.path.isfile(potential_file):
                file_path = potential_file
            else:
                # SPA fallback for React Router routes like /login, /dashboard
                file_path = os.path.join(DIST_DIR, "index.html")
        
        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        if file_path.endswith(".html"):
            mime_type = "text/html; charset=utf-8"
        elif file_path.endswith(".js"):
            mime_type = "application/javascript; charset=utf-8"
        elif file_path.endswith(".css"):
            mime_type = "text/css; charset=utf-8"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            if "assets" in file_path:
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            else:
                self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_handle(self):
        path_lower = self.path.lower()
        if (
            path_lower.startswith("/api/")
            or path_lower in ("/docs", "/redoc", "/openapi.json", "/health")
            or path_lower.startswith("/docs/")
        ):
            self.do_proxy_backend()
        else:
            self.do_serve_static()

    do_GET = do_handle
    do_POST = do_handle
    do_PUT = do_handle
    do_DELETE = do_handle
    do_PATCH = do_handle
    do_OPTIONS = do_handle
    do_HEAD = do_handle

    def log_message(self, format, *args):
        # Keep console uncluttered
        pass

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), FastReverseProxyAndStaticServer)
    print(f"Unified Fast Gateway active on http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
