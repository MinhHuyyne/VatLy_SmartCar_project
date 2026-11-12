"""Chế độ tự động: đi thẳng, gặp vật cản thì dừng - quét - né (việc 9)."""
import time
from typing import Callable, Optional

from .protocol import Direction


def decide(left_cm: float, right_cm: float, need_cm: float) -> Optional[Direction]:
    """Chọn hướng thoáng hơn; None nếu cả hai bên đều bị chặn."""
    options = [(left_cm, Direction.LEFT), (right_cm, Direction.RIGHT)]
    options = [o for o in options if o[0] >= need_cm]
    if not options:
        return None
    return max(options, key=lambda o: o[0])[1]


class AutoPilot:
    def __init__(self, drive, scanner, cfg, notify: Callable, should_abort: Callable[[], bool]):
        self.drive = drive
        self.scanner = scanner
        self.cfg = cfg
        self.notify = notify
        self.should_abort = should_abort
        self.last_distance = None
        self.reset()

    def reset(self):
        self.retries = 0
        self.blocked = False
        self.state = "cruising"

    def _wait(self, seconds: float) -> bool:
        """Ngủ nhưng thoát sớm nếu có lệnh mới (vd. đổi chế độ)."""
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self.should_abort():
                return False
            time.sleep(0.02)
        return True

    def step(self):
        if self.blocked:
            return
        cfg = self.cfg
        d = self.scanner.front()
        self.last_distance = d

        if d >= cfg.threshold_cm:
            self.drive.apply(Direction.FORWARD)
            self.state = "cruising"
            return

        # Gặp vật cản
        self.drive.stop()
        self.state = "scanning"
        left, right = self.scanner.scan_sides()
        choice = decide(left, right, cfg.threshold_cm * cfg.clear_factor)

        if choice is None:
            self.retries += 1
            if self.retries > cfg.max_retries:
                self.blocked = True
                self.state = "blocked"
                self.notify("error", "blocked",
                            f"Không tìm được đường (trái {left} cm, phải {right} cm). Xe đã dừng.")
                return
            self.state = "reversing"
            self.drive.apply(Direction.BACKWARD)
            self._wait(cfg.backup_s)
            self.drive.stop()
            return

        self.retries = 0
        self.state = f"turning_{choice.value}"
        self.drive.apply(choice)
        self._wait(cfg.turn_s)
        self.drive.stop()
        # Vòng lặp sau sẽ đo lại phía trước rồi mới đi tiếp.
