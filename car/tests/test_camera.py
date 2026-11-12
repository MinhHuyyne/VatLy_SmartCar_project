"""Test server MJPEG bằng khung hình giả (không cần Picamera2)."""
import threading
import time
import urllib.request

from smartcar.camera import _FrameBuffer, _make_handler, _Server

JPEG = b"\xff\xd8fake-jpeg\xff\xd9"


def _serve():
    frames = _FrameBuffer()
    httpd = _Server(("127.0.0.1", 0), _make_handler(frames, max_clients=1))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    def feed():
        while True:
            frames.write(JPEG)
            time.sleep(0.05)

    threading.Thread(target=feed, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


def test_snapshot_and_stream():
    httpd, base = _serve()
    try:
        r = urllib.request.urlopen(f"{base}/snapshot.jpg", timeout=3)
        assert r.headers["Content-Type"] == "image/jpeg"
        assert r.headers["Access-Control-Allow-Origin"] == "*"
        assert r.read() == JPEG

        s = urllib.request.urlopen(f"{base}/stream.mjpg", timeout=3)
        assert s.headers["Content-Type"].startswith("multipart/x-mixed-replace")
        chunk = s.read(200)
        assert b"--FRAME" in chunk and JPEG in chunk
        s.close()
    finally:
        httpd.shutdown()


def test_unknown_path_404():
    httpd, base = _serve()
    try:
        urllib.request.urlopen(f"{base}/abc", timeout=3)
        assert False, "phải trả 404"
    except urllib.error.HTTPError as e:
        assert e.code == 404
    finally:
        httpd.shutdown()
