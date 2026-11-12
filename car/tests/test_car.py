"""Test logic xe bằng phần cứng giả lập — không cần Pi, không cần broker."""
import time

from smartcar.autopilot import decide
from smartcar.config import Config
from smartcar.controller import CarController
from smartcar.protocol import Direction, Mode
from smartcar.sim import SimDrive


class FakeScanner:
    def __init__(self, front=100.0, left=100.0, right=100.0):
        self.front_cm, self.left_cm, self.right_cm = front, left, right

    def center(self):
        pass

    def front(self):
        return self.front_cm

    def scan_sides(self):
        return self.left_cm, self.right_cm


def make(front=100.0, left=100.0, right=100.0):
    cfg = Config()
    cfg.turn_s = cfg.backup_s = 0.0
    sent = []
    drive = SimDrive(cfg.speed)
    scanner = FakeScanner(front, left, right)
    ctrl = CarController(drive, scanner, cfg, publish=lambda k, p: sent.append((k, p)))
    return ctrl, drive, scanner, sent


def acks(sent):
    return [p for k, p in sent if k == "ack"]


# ---- decide() ----
def test_decide_picks_wider_side():
    assert decide(80, 40, 30) == Direction.LEFT
    assert decide(40, 90, 30) == Direction.RIGHT


def test_decide_blocked():
    assert decide(10, 20, 30) is None


# ---- thủ công ----
def test_manual_move_and_ack():
    ctrl, drive, _, sent = make()
    ctrl.handle({"type": "move", "dir": "forward", "id": "a1"})
    assert drive.direction == Direction.FORWARD
    assert acks(sent)[-1]["id"] == "a1" and acks(sent)[-1]["ok"]


def test_manual_safety_stop_near_obstacle():
    ctrl, drive, scanner, sent = make(front=100)
    ctrl.handle({"type": "move", "dir": "forward"})
    scanner.front_cm = 10
    ctrl.tick()
    assert drive.direction == Direction.STOP
    assert any(k == "event" and p["code"] == "obstacle_stop" for k, p in sent)


def test_manual_refuses_forward_when_too_close():
    ctrl, drive, _, sent = make(front=10)
    ctrl.tick()
    ctrl.handle({"type": "move", "dir": "forward", "id": "x"})
    assert drive.direction == Direction.STOP
    assert acks(sent)[-1]["error"] == "obstacle"


def test_heartbeat_timeout_stops_car():
    ctrl, drive, _, sent = make()
    ctrl.cfg.heartbeat_timeout_s = 0.01
    ctrl.handle({"type": "move", "dir": "backward"})
    time.sleep(0.03)
    ctrl.tick()
    assert drive.direction == Direction.STOP


# ---- chuyển chế độ ----
def test_mode_switch_stops_first_and_ignores_manual_in_auto():
    ctrl, drive, _, sent = make()
    ctrl.handle({"type": "move", "dir": "backward"})
    ctrl.handle({"type": "mode", "mode": "auto"})
    assert ctrl.mode == Mode.AUTO and drive.direction == Direction.STOP
    ctrl.handle({"type": "move", "dir": "left", "id": "m"})
    assert acks(sent)[-1]["error"] == "auto_mode"


# ---- tự động ----
def test_auto_cruises_when_clear():
    ctrl, drive, _, _ = make(front=100)
    ctrl.handle({"type": "mode", "mode": "auto"})
    ctrl.tick()
    assert drive.direction == Direction.FORWARD


def test_auto_turns_to_clear_side():
    ctrl, drive, _, _ = make(front=10, left=20, right=120)
    ctrl.handle({"type": "mode", "mode": "auto"})
    ctrl.tick()
    assert Direction.RIGHT in drive.history


def test_auto_backs_up_then_reports_blocked():
    ctrl, drive, _, sent = make(front=10, left=10, right=10)
    ctrl.handle({"type": "mode", "mode": "auto"})
    for _ in range(ctrl.cfg.max_retries + 1):
        ctrl.tick()
    assert Direction.BACKWARD in drive.history
    assert ctrl.state == "blocked" and drive.direction == Direction.STOP
    assert any(k == "event" and p["code"] == "blocked" for k, p in sent)


def test_config_validation():
    ctrl, drive, _, sent = make()
    ctrl.handle({"type": "config", "threshold_cm": 40, "speed": 0.9, "id": "c"})
    assert ctrl.cfg.threshold_cm == 40
    assert drive.speed == 0.9
    ctrl.handle({"type": "config", "threshold_cm": 999, "id": "d"})
    assert acks(sent)[-1]["ok"] is False


def test_speed_range_10_to_100_percent():
    ctrl, drive, _, sent = make()
    for ok in (0.1, 0.55, 1.0):
        ctrl.handle({"type": "config", "speed": ok, "id": "s"})
        assert acks(sent)[-1]["ok"] and drive.speed == ok
    for bad in (0.05, 1.5, 0):
        ctrl.handle({"type": "config", "speed": bad, "id": "b"})
        assert acks(sent)[-1]["ok"] is False
    assert drive.speed == 1.0


def test_speed_to_duty_mapping():
    from smartcar.config import speed_to_duty
    assert speed_to_duty(0.1, 0.3, 0.6) == 0.3     # 10%  -> chậm nhất vẫn quay
    assert speed_to_duty(1.0, 0.3, 0.6) == 0.6     # 100% -> giới hạn an toàn
    assert speed_to_duty(0.55, 0.3, 0.6) == 0.45   # ở giữa
    assert speed_to_duty(1.0, 0.3, 1.0) == 1.0     # nếu cho phép full điện áp
