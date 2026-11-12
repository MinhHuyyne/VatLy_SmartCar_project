"""Kết nối MQTT phía xe (việc 7). Dùng paho-mqtt 2.x."""
import json
import logging

import paho.mqtt.client as mqtt

from .protocol import topics

log = logging.getLogger(__name__)


class MqttLink:
    def __init__(self, cfg):
        self.cfg = cfg
        self.t = topics(cfg.car_id)
        self.on_command = lambda cmd: None
        self.on_lost = lambda: None
        self.camera_info: dict = {"enabled": False}

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"smartcar-{cfg.car_id}")
        if cfg.mqtt_user:
            self.client.username_pw_set(cfg.mqtt_user, cfg.mqtt_pass)
        # Last Will: broker tự báo "offline" nếu xe rớt mạng đột ngột
        self.client.will_set(self.t["status"], "offline", qos=1, retain=True)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=5)

    def start(self):
        self.client.connect_async(self.cfg.mqtt_host, self.cfg.mqtt_port, keepalive=5)
        self.client.loop_start()

    def stop(self):
        self.client.publish(self.t["camera"], json.dumps({"enabled": False}), qos=1, retain=True)
        self.client.publish(self.t["status"], "offline", qos=1, retain=True)
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, kind: str, payload: dict):
        qos = 0 if kind == "telemetry" else 1
        self.client.publish(self.t[kind], json.dumps(payload, ensure_ascii=False), qos=qos)

    def publish_camera(self, info: dict):
        self.camera_info = info
        self.client.publish(self.t["camera"], json.dumps(info), qos=1, retain=True)

    # ---- callbacks (chạy trong luồng của paho) ----
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        log.info("MQTT connected: %s", reason_code)
        client.subscribe(self.t["cmd"], qos=1)
        client.publish(self.t["status"], "online", qos=1, retain=True)
        self.publish_camera(self.camera_info)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        log.warning("MQTT disconnected: %s", reason_code)
        self.on_lost()

    def _on_message(self, client, userdata, msg):
        try:
            cmd = json.loads(msg.payload)
            if not isinstance(cmd, dict):
                raise ValueError("payload phải là JSON object")
        except ValueError as e:
            log.warning("Lệnh không hợp lệ: %s", e)
            return
        self.on_command(cmd)
