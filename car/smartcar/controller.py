"""Bộ điều phối trung tâm (việc 10, 12).

- Lệnh MQTT được đưa vào hàng đợi và xử lý trong MỘT vòng lặp duy nhất,
  nên chế độ thủ công và tự động không bao giờ chạy chồng nhau.
- Đổi chế độ luôn dừng xe trước.
- Dừng an toàn: quá gần vật cản (kể cả thủ công) hoặc mất heartbeat/kết nối.
"""
import logging
import queue
import time

from .autopilot import AutoPilot
from .config import SPEED_MAX, SPEED_MIN
from .protocol import CmdType, Direction, Mode

log = logging.getLogger(__name__)


class CarController:
    def __init__(self, drive, scanner, cfg, publish):
        self.drive = drive
        self.scanner = scanner
        self.cfg = cfg
        self.publish = publish          # publish(kind: str, payload: dict)
        self.mode = Mode.MANUAL
        self.state = "idle"
        self.distance_cm = None
        self.last_heartbeat = time.monotonic()
        self._cmds: "queue.Queue[dict]" = queue.Queue()
        self._running = False
        self._last_telemetry = 0.0
        self.autopilot = AutoPilot(drive, scanner, cfg, notify=self.event,
                                   should_abort=lambda: not self._cmds.empty())

    # ---- gọi từ luồng MQTT (thread-safe) ----
    def submit(self, cmd: dict):
        self._cmds.put(cmd)

    def on_link_lost(self):
        self._cmds.put({"type": "_link_lost"})

    # ---- vòng lặp chính ----
    def run(self):
        self._running = True
        while self._running:
            self.process_pending()
            self.tick()
            self.maybe_send_telemetry()
            time.sleep(self.cfg.loop_period_s)

    def stop(self):
        self._running = False
        self.drive.stop()

    def process_pending(self):
        while True:
            try:
                cmd = self._cmds.get_nowait()
            except queue.Empty:
                return
            self.handle(cmd)

    def tick(self):
        if self.mode == Mode.AUTO:
            self.autopilot.step()
            self.distance_cm = self.autopilot.last_distance
            self.state = self.autopilot.state
            return

        # Thủ công: giám sát an toàn
        self.distance_cm = self.scanner.front()
        moving = self.drive.direction != Direction.STOP
        if self.drive.direction == Direction.FORWARD and self.distance_cm < self.cfg.threshold_cm:
            self.drive.stop()
            self.event("warn", "obstacle_stop", f"Vật cản cách {self.distance_cm} cm — xe tự dừng.")
        elif moving and time.monotonic() - self.last_heartbeat > self.cfg.heartbeat_timeout_s:
            self.drive.stop()
            self.event("warn", "heartbeat_lost", "Mất tín hiệu từ website — xe tự dừng.")
        self.state = "idle" if self.drive.direction == Direction.STOP else f"moving_{self.drive.direction.value}"

    # ---- xử lý lệnh ----
    def handle(self, cmd: dict):
        t = cmd.get("type")
        cid = cmd.get("id")
        now = time.monotonic()

        if t == CmdType.HEARTBEAT:
            self.last_heartbeat = now
            return
        if t == "_link_lost":
            self.drive.stop()
            log.warning("MQTT mất kết nối — dừng xe")
            return

        self.last_heartbeat = now
        try:
            if t == CmdType.MODE:
                new_mode = Mode(cmd["mode"])
                self.drive.stop()
                self.scanner.center()
                self.mode = new_mode
                self.autopilot.reset()
                self.state = "idle"
                self.ack(cid, True)

            elif t == CmdType.MOVE:
                d = Direction(cmd["dir"])
                if self.mode == Mode.AUTO:
                    self.ack(cid, False, "auto_mode")
                elif d == Direction.FORWARD and self.distance_cm is not None \
                        and self.distance_cm < self.cfg.threshold_cm:
                    self.drive.stop()
                    self.ack(cid, False, "obstacle")
                else:
                    self.drive.apply(d)
                    self.ack(cid, True)

            elif t == CmdType.CONFIG:
                if "threshold_cm" in cmd:
                    v = float(cmd["threshold_cm"])
                    if not 5 <= v <= 150:
                        raise ValueError("threshold_cm phải trong [5, 150]")
                    self.cfg.threshold_cm = v
                if "speed" in cmd:
                    s = float(cmd["speed"])
                    if not SPEED_MIN <= s <= SPEED_MAX:
                        raise ValueError("speed phải trong [0.1, 1.0] (10-100%)")
                    self.drive.set_speed(s)
                    self.cfg.speed = self.drive.speed
                self.ack(cid, True)

            else:
                self.ack(cid, False, "unknown_command")
        except (KeyError, ValueError) as e:
            self.ack(cid, False, f"bad_request: {e}")

    # ---- gửi lên MQTT ----
    def snapshot(self) -> dict:
        return {
            "mode": self.mode.value,
            "state": self.state,
            "direction": self.drive.direction.value,
            "distance_cm": self.distance_cm,
            "threshold_cm": self.cfg.threshold_cm,
            "speed": self.drive.speed,
            "ts": time.time(),
        }

    def ack(self, cmd_id, ok: bool, error: str = None):
        payload = {"id": cmd_id, "ok": ok, **self.snapshot()}
        if error:
            payload["error"] = error
        self.publish("ack", payload)

    def event(self, level: str, code: str, msg: str):
        log.info("[%s] %s: %s", level, code, msg)
        self.publish("event", {"level": level, "code": code, "msg": msg, "ts": time.time()})

    def maybe_send_telemetry(self):
        now = time.monotonic()
        if now - self._last_telemetry >= self.cfg.telemetry_period_s:
            self._last_telemetry = now
            self.publish("telemetry", self.snapshot())
