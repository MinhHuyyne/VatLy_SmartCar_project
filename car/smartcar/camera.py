"""Phát hình từ camera OV5647 dạng MJPEG qua HTTP.

- Dùng Picamera2 + bộ mã hoá MJPEG phần cứng của Pi Zero 2 W (nhẹ CPU).
- Hình đi thẳng từ Pi tới trình duyệt (không qua MQTT vì MQTT không hợp với video).
- Địa chỉ luồng được gửi lên topic `camera` (retained) để website tự biết mà hiển thị.

Endpoint:
    http://<IP-Pi>:8001/stream.mjpg   luồng video
    http://<IP-Pi>:8001/snapshot.jpg  1 khung hình
"""
import io
import logging
import socket
import threading
from http import server
from socketserver import ThreadingMixIn

log = logging.getLogger(__name__)


class _FrameBuffer(io.BufferedIOBase):
    """Giữ khung hình JPEG mới nhất, báo cho các client đang chờ."""

    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = bytes(buf)
            self.condition.notify_all()
        return len(buf)

    def wait_frame(self, timeout=2.0):
        with self.condition:
            self.condition.wait(timeout)
            return self.frame


class _Server(ThreadingMixIn, server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _make_handler(frames: _FrameBuffer, max_clients: int):
    clients = threading.BoundedSemaphore(max_clients)

    class Handler(server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # tắt log mỗi request
            pass

        def _headers(self, status=200, ctype="text/plain"):
            self.send_response(status)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", ctype)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/snapshot.jpg":
                frame = frames.wait_frame()
                if not frame:
                    self._headers(503); self.end_headers(); return
                self._headers(ctype="image/jpeg")
                self.send_header("Content-Length", str(len(frame)))
                self.end_headers()
                self.wfile.write(frame)
                return

            if path != "/stream.mjpg":
                self._headers(404); self.end_headers(); return

            if not clients.acquire(blocking=False):
                self._headers(503); self.end_headers()
                self.wfile.write(b"Qua nhieu nguoi xem")
                return
            try:
                self._headers(ctype="multipart/x-mixed-replace; boundary=FRAME")
                self.end_headers()
                while True:
                    frame = frames.wait_frame()
                    if frame is None:
                        continue
                    self.wfile.write(b"--FRAME\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass  # trình duyệt đóng tab
            finally:
                clients.release()

    return Handler


def guess_ip(towards_host: str) -> str:
    """IP của Pi trong mạng LAN (theo hướng tới broker)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect((towards_host if towards_host not in ("localhost", "127.0.0.1") else "8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class CameraStreamer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.frames = _FrameBuffer()
        self.picam = None
        self.httpd = None

    def start(self) -> dict:
        """Bật camera + HTTP server. Trả về thông tin để gửi lên MQTT."""
        from libcamera import Transform
        from picamera2 import Picamera2
        from picamera2.encoders import MJPEGEncoder
        from picamera2.outputs import FileOutput

        c = self.cfg
        self.picam = Picamera2()
        config = self.picam.create_video_configuration(
            main={"size": (c.camera_width, c.camera_height)},
            controls={"FrameRate": c.camera_fps},
            transform=Transform(hflip=c.camera_hflip, vflip=c.camera_vflip),
        )
        self.picam.configure(config)
        self.picam.start_recording(MJPEGEncoder(), FileOutput(self.frames))

        self.httpd = _Server(("0.0.0.0", c.camera_port), _make_handler(self.frames, c.camera_max_clients))
        threading.Thread(target=self.httpd.serve_forever, daemon=True, name="camera-http").start()

        base = c.camera_public_url or f"http://{guess_ip(c.mqtt_host)}:{c.camera_port}"
        info = {
            "enabled": True,
            "stream_url": f"{base}/stream.mjpg",
            "snapshot_url": f"{base}/snapshot.jpg",
            "width": c.camera_width,
            "height": c.camera_height,
            "fps": c.camera_fps,
        }
        log.info("Camera đang phát: %s", info["stream_url"])
        return info

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
        if self.picam:
            try:
                self.picam.stop_recording()
            finally:
                self.picam.close()
