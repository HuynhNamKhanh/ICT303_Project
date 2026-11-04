import functools
import http.server
import os
import socketserver
import threading
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = "Com_nha_application_final.html"
PORT = 8000


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # no logging


def main():
    if not os.path.exists(os.path.join(BASE_DIR, HTML_FILE)):
        print(f"Could not find {HTML_FILE} in {BASE_DIR}")
        return

    handler = functools.partial(QuietHandler, directory=BASE_DIR)
    socketserver.TCPServer.allow_reuse_address = True

    # If port 8000 is in use, try the next 20 ports
    server = None
    for port in range(PORT, PORT + 20):
        try:
            server = socketserver.TCPServer(("127.0.0.1", port), handler)
            break
        except OSError:
            continue
    if server is None:
        print("Could not find an available port.")
        return

    url = f"http://127.0.0.1:{port}/{HTML_FILE}"
    print(f"Website is running at: {url}")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWebsite has been stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
