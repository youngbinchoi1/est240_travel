#!/usr/bin/env python3
"""Local web server that supports HTTP Range requests.

Browsers REQUIRE Range support (HTTP 206 Partial Content) to play <video>.
Python's built-in `http.server` does NOT support Range, which makes embedded
videos fail to load. Run this instead:

    python3 serve.py

then open  http://localhost:8000/expertise.html
"""
import http.server
import os
import re
import socketserver

PORT = 8000


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()

        ctype = self.guess_type(path)
        fs = os.stat(path)
        size = fs.st_size
        range_header = self.headers.get("Range")

        if range_header is None:
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return open(path, "rb")

        m = re.match(r"bytes=(\d*)-(\d*)", range_header)
        start, end = m.group(1), m.group(2)
        start = int(start) if start else 0
        end = int(end) if end else size - 1
        end = min(end, size - 1)
        length = end - start + 1

        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        self._range_remaining = length
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_range_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        while remaining > 0:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


os.chdir(os.path.dirname(os.path.abspath(__file__)))
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), RangeRequestHandler) as httpd:
    print(f"Serving at http://localhost:{PORT}/expertise.html  (Ctrl+C to stop)")
    httpd.serve_forever()
