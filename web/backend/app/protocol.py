"""Bản sao giao thức của car/smartcar/protocol.py — giữ đồng bộ hai bên."""

ALLOWED_CMD_TYPES = {"move", "mode", "config", "heartbeat"}


def topics(car_id: str) -> dict:
    base = f"smartcar/{car_id}"
    return {
        "cmd": f"{base}/cmd",
        "ack": f"{base}/ack",
        "telemetry": f"{base}/telemetry",
        "event": f"{base}/event",
        "status": f"{base}/status",
        "camera": f"{base}/camera",
    }
