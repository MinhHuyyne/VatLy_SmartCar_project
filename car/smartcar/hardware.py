"""Lớp phần cứng thật trên Raspberry Pi (gpiozero).

Chỉ import gpiozero bên trong hàm để code còn lại chạy được trên laptop.
"""
import time

from .config import clamp_speed, speed_to_duty
from .protocol import Direction


class DriveTrain:
    """2 kênh L298N: kênh A = 2 motor bên trái, kênh B = 2 motor bên phải."""

    def __init__(self, pins, speed: float, min_duty: float, max_duty: float):
        from gpiozero import Motor

        self.left = Motor(forward=pins.in1, backward=pins.in2, enable=pins.ena, pwm=True)
        self.right = Motor(forward=pins.in3, backward=pins.in4, enable=pins.enb, pwm=True)
        self.min_duty, self.max_duty = min_duty, max_duty
        self.speed = clamp_speed(speed)   # 0.1..1.0 (10..100%)
        self.direction = Direction.STOP

    def apply(self, d: Direction):
        s = speed_to_duty(self.speed, self.min_duty, self.max_duty)  # duty PWM thực tế
        if d == Direction.FORWARD:
            self.left.forward(s); self.right.forward(s)
        elif d == Direction.BACKWARD:
            self.left.backward(s); self.right.backward(s)
        elif d == Direction.LEFT:      # quay tại chỗ sang trái
            self.left.backward(s); self.right.forward(s)
        elif d == Direction.RIGHT:     # quay tại chỗ sang phải
            self.left.forward(s); self.right.backward(s)
        else:
            self.left.stop(); self.right.stop()
            d = Direction.STOP
        self.direction = d

    def stop(self):
        self.apply(Direction.STOP)

    def set_speed(self, s: float):
        self.speed = clamp_speed(s)
        if self.direction != Direction.STOP:
            self.apply(self.direction)


class Ultrasonic:
    def __init__(self, trig: int, echo: int, max_cm: float):
        from gpiozero import DistanceSensor

        self._s = DistanceSensor(echo=echo, trigger=trig, max_distance=max_cm / 100, queue_len=3)

    def read_cm(self) -> float:
        return round(self._s.distance * 100, 1)


class Scanner:
    """Cảm biến siêu âm gắn trên servo SG90. Góc dương = bên trái."""

    def __init__(self, sensor, servo_pin: int, side_angle: float, settle_s: float):
        from gpiozero import AngularServo

        self.sensor = sensor
        self.servo = AngularServo(servo_pin, min_angle=-90, max_angle=90,
                                  min_pulse_width=0.0005, max_pulse_width=0.0024)
        self.side_angle = side_angle
        self.settle_s = settle_s
        self._angle = None
        self.center()

    def _look(self, angle: float):
        if angle != self._angle:
            self.servo.angle = angle
            time.sleep(self.settle_s)
            self._angle = angle

    def center(self):
        self._look(0)

    def front(self) -> float:
        self._look(0)
        return self.sensor.read_cm()

    def scan_sides(self):
        self._look(self.side_angle)
        left = self.sensor.read_cm()
        self._look(-self.side_angle)
        right = self.sensor.read_cm()
        self._look(0)
        return left, right


def build(cfg):
    p = cfg.pins
    drive = DriveTrain(p, cfg.speed, cfg.min_duty, cfg.max_duty)
    sensor = Ultrasonic(p.trig, p.echo, cfg.max_distance_cm)
    scanner = Scanner(sensor, p.servo, cfg.side_angle, cfg.servo_settle_s)
    return drive, scanner
