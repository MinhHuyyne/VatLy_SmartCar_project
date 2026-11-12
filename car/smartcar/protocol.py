"""Giao thức MQTT dùng chung giữa xe và backend.

Xem chi tiết: docs/mqtt-protocol.md. Backend có bản sao các hằng số này
trong web/backend/app/protocol.py — khi sửa ở đây nhớ sửa cả bên đó.
"""
from enum import Enum


class Mode(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"


class Direction(str, Enum):
    FORWARD = "forward"
    BACKWARD = "backward"
    LEFT = "left"
    RIGHT = "right"
    STOP = "stop"


class CmdType(str, Enum):
    MOVE = "move"
    MODE = "mode"
    CONFIG = "config"
    HEARTBEAT = "heartbeat"


def topics(car_id: str) -> dict:
    base = f"smartcar/{car_id}"
    return {
        "cmd": f"{base}/cmd",              # web -> xe   (QoS 1, heartbeat QoS 0)
        "ack": f"{base}/ack",              # xe -> web   phản hồi xác nhận lệnh
        "telemetry": f"{base}/telemetry",  # xe -> web   khoảng cách, trạng thái (định kỳ)
        "event": f"{base}/event",          # xe -> web   cảnh báo / lỗi (bị chặn, mất kết nối...)
        "status": f"{base}/status",        # xe -> web   "online"/"offline" (retained + LWT)
        "camera": f"{base}/camera",        # xe -> web   địa chỉ luồng camera (retained)
    }
