"""Phần cứng giả lập — chạy trên laptop khi SMARTCAR_SIM=1.

Giúp làm website / MQTT / thuật toán tự động khi chưa có xe.
"""
import random

from .config import clamp_speed
from .protocol import Direction


class SimDrive:
    def __init__(self, speed: float = 0.5):
        self.speed = clamp_speed(speed)
        self.direction = Direction.STOP
        self.history = []

    def apply(self, d: Direction):
        if d != self.direction:
            self.history.append(d)
        self.direction = d

    def stop(self):
        self.apply(Direction.STOP)

    def set_speed(self, s: float):
        self.speed = clamp_speed(s)


class SimWorld:
    """Thế giới 1 chiều đơn giản: đi thẳng thì vật cản tiến lại gần."""

    def __init__(self, drive: SimDrive, seed=None):
        self.drive = drive
        self.rng = random.Random(seed)
        self.front_cm = 120.0
        self.left_cm = 80.0
        self.right_cm = 80.0

    def tick(self):
        d = self.drive.direction
        step = 40 * self.drive.speed  # cm mỗi lần đo
        if d == Direction.FORWARD:
            self.front_cm = max(3.0, self.front_cm - step)
        elif d == Direction.BACKWARD:
            self.front_cm += step
        elif d in (Direction.LEFT, Direction.RIGHT):
            self._new_heading()

    def _new_heading(self):
        self.front_cm = self.rng.uniform(30, 200)
        self.left_cm = self.rng.uniform(10, 150)
        self.right_cm = self.rng.uniform(10, 150)


class SimScanner:
    def __init__(self, world: SimWorld):
        self.world = world

    def center(self):
        pass

    def front(self) -> float:
        self.world.tick()
        return round(self.world.front_cm, 1)

    def scan_sides(self):
        return round(self.world.left_cm, 1), round(self.world.right_cm, 1)


def build(cfg):
    drive = SimDrive(cfg.speed)
    return drive, SimScanner(SimWorld(drive))
