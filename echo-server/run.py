# Reflects the requests from HTTP methods GET, POST, PUT, and DELETE
#
# Based on https://gist.github.com/1kastner/e083f9e813c0464e6a2ec8910553e632

import os
import base64
import json
import threading

from http.server import HTTPServer, BaseHTTPRequestHandler


def flush_print(s):
    print(s, flush=True)


def decodeb64(s):
    return str(base64.b64decode(s), 'utf-8')


class StoppableHTTPServer(HTTPServer):
    def run(self):
        try:
            self.serve_forever()
        except Exception:  # pylint: disable=W0703
            pass
        finally:
            self.server_close()


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        flush_print(f"\n{self.command} {self.path}")

        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        flush_print(f"\n{self.command} {self.path}")

        content_length = self.headers.get('Content-Length')
        length = int(content_length) if content_length else 0
        payload = self.rfile.read(length)

        content_type = self.headers.get('Content-Type')
        if content_type == 'application/json':
            payload_json = json.loads(str(payload, 'utf-8'))
            if payload_json.get('output'):
                payload_json['output'] = decodeb64(payload_json['output'])
            if payload_json.get('message'):
                payload_json['message'] = decodeb64(payload_json['message'])

            payload = json.dumps(payload_json)

        flush_print(f"  {payload}")

        self.send_response(200)
        self.end_headers()

    do_PUT = do_POST
    do_DELETE = do_GET


def main():
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    print(f'Listening on {host}:{port}')
    server = StoppableHTTPServer((host, port), RequestHandler)

    # Start processing requests
    thread = threading.Thread(None, server.run)
    thread.start()


if __name__ == "__main__":
    main()
