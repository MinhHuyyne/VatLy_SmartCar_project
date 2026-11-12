"""Backend: cầu nối WebSocket (trình duyệt) <-> MQTT (xe).  (việc 8, 11)

Luồng:  Website --WS--> Backend --MQTT cmd--> Xe
        Xe --MQTT ack/telemetry/event/status--> Backend --WS--> Website
Chạy:   uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import asyncio
import json
import logging
import os
import socket
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .protocol import ALLOWED_CMD_TYPES, topics

log = logging.getLogger("backend")
logging.basicConfig(level=logging.INFO)

CAR_ID = os.getenv("SMARTCAR_ID", "car01")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
PORT = int(os.getenv("PORT", "8000"))
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parents[2] / "frontend" / "dist"))

T = topics(CAR_ID)
TOPIC_TO_KIND = {v: k for k, v in T.items() if k != "cmd"}


class Hub:
    def __init__(self):
        self.clients: set[WebSocket] = set()
        self.queue: asyncio.Queue = asyncio.Queue()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.broker_connected = False
        self.last = {"status": "unknown", "telemetry": None, "camera": {"enabled": False}}

    def push_threadsafe(self, msg: dict):
        if self.loop:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, msg)

    async def broadcaster(self):
        while True:
            msg = await self.queue.get()
            data = json.dumps(msg, ensure_ascii=False)
            for ws in list(self.clients):
                try:
                    await ws.send_text(data)
                except Exception:
                    self.clients.discard(ws)


hub = Hub()
mq = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"smartcar-backend-{uuid.uuid4().hex[:6]}")


def on_connect(client, userdata, flags, reason_code, properties):
    hub.broker_connected = True
    for kind, topic in T.items():
        if kind != "cmd":
            client.subscribe(topic, qos=1)
    hub.push_threadsafe({"kind": "broker", "data": {"connected": True}})


def on_disconnect(client, userdata, flags, reason_code, properties):
    hub.broker_connected = False
    hub.push_threadsafe({"kind": "broker", "data": {"connected": False}})


def on_message(client, userdata, msg):
    kind = TOPIC_TO_KIND.get(msg.topic)
    if not kind:
        return
    raw = msg.payload.decode("utf-8", "replace")
    data = raw if kind == "status" else json.loads(raw)
    if kind in hub.last:
        hub.last[kind] = data
    hub.push_threadsafe({"kind": kind, "data": data})


mq.on_connect, mq.on_disconnect, mq.on_message = on_connect, on_disconnect, on_message


def lan_urls() -> list[str]:
    """Các địa chỉ trong mạng LAN để mở trên điện thoại."""
    ips = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    ips.discard("127.0.0.1")
    return [f"http://{ip}:{PORT}" for ip in sorted(ips)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    hub.loop = asyncio.get_running_loop()
    task = asyncio.create_task(hub.broadcaster())
    mq.connect_async(MQTT_HOST, MQTT_PORT, keepalive=10)
    mq.loop_start()
    log.info("MQTT -> %s:%s, car=%s", MQTT_HOST, MQTT_PORT, CAR_ID)
    urls = lan_urls()
    if urls:
        log.info("📱 Mở trên điện thoại (cùng Wi-Fi): %s", "  |  ".join(urls))
    if not (FRONTEND_DIR / "index.html").exists():
        log.warning("Chưa có giao diện ở %s — chạy `npm run build` trong web/frontend", FRONTEND_DIR)
    yield
    mq.loop_stop()
    task.cancel()


app = FastAPI(title="Smart Car Backend", lifespan=lifespan)


@app.get("/api/connect")
def connect_info():
    return {"urls": lan_urls()}


@app.get("/api/health")
def health():
    return {"broker_connected": hub.broker_connected, "car_status": hub.last["status"], "car_id": CAR_ID}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    hub.clients.add(ws)
    await ws.send_text(json.dumps({"kind": "hello", "data": {
        "car_id": CAR_ID, "broker_connected": hub.broker_connected, **hub.last}}, ensure_ascii=False))
    try:
        while True:
            try:
                cmd = json.loads(await ws.receive_text())
            except ValueError:
                continue
            if not isinstance(cmd, dict) or cmd.get("type") not in ALLOWED_CMD_TYPES:
                continue
            if cmd["type"] == "heartbeat":
                mq.publish(T["cmd"], json.dumps(cmd), qos=0)
                continue
            cmd.setdefault("id", uuid.uuid4().hex[:8])
            mq.publish(T["cmd"], json.dumps(cmd), qos=1)
            await ws.send_text(json.dumps({"kind": "sent", "data": {"id": cmd["id"]}}))
    except WebSocketDisconnect:
        pass
    finally:
        hub.clients.discard(ws)


# Phục vụ bản build React (web/frontend/dist, tạo bằng `npm run build`) ở "/"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
