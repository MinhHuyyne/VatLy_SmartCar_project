"""Cấu hình xe, đọc từ biến môi trường (xem car/.env.example)."""
import os
from dataclasses import dataclass, field


def _env(name, default, cast=str):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    if cast is bool:
        return raw.lower() in ("1", "true", "yes", "on")
    return cast(raw)


@dataclass
class Pins:
    """Số chân GPIO theo chuẩn BCM. Xem docs/wiring.md."""
    ena: int = 12   # PWM bánh trái  (L298N ENA - nhớ tháo jumper)
    in1: int = 5
    in2: int = 6
    enb: int = 13   # PWM bánh phải  (L298N ENB - nhớ tháo jumper)
    in3: int = 20
    in4: int = 21
    trig: int = 23  # HC-SR04 TRIG
    echo: int = 24  # HC-SR04 ECHO (QUA MẠCH CHIA ÁP 5V -> 3.3V!)
    servo: int = 18  # SG90 tín hiệu


@dataclass
class Config:
    car_id: str = field(default_factory=lambda: _env("SMARTCAR_ID", "car01"))
    sim: bool = field(default_factory=lambda: _env("SMARTCAR_SIM", False, bool))

    mqtt_host: str = field(default_factory=lambda: _env("MQTT_HOST", "localhost"))
    mqtt_port: int = field(default_factory=lambda: _env("MQTT_PORT", 1883, int))
    mqtt_user: str = field(default_factory=lambda: _env("MQTT_USER", ""))
    mqtt_pass: str = field(default_factory=lambda: _env("MQTT_PASS", ""))

    # Điều khiển
    # Tốc độ người dùng chọn: 0.1..1.0 (= 10..100% trên website).
    # Quy đổi sang duty PWM: 10% -> MIN_DUTY (chậm nhất mà motor vẫn quay), 100% -> MAX_DUTY.
    speed: float = field(default_factory=lambda: _env("SPEED", 0.5, float))
    min_duty: float = field(default_factory=lambda: _env("MIN_DUTY", 0.3, float))
    max_duty: float = field(default_factory=lambda: _env("MAX_DUTY", 0.6, float))  # bảo vệ motor TT 3-6V khi dùng pin ~11V
    threshold_cm: float = field(default_factory=lambda: _env("THRESHOLD_CM", 25.0, float))
    heartbeat_timeout_s: float = field(default_factory=lambda: _env("HEARTBEAT_TIMEOUT_S", 1.5, float))
    loop_period_s: float = 0.05
    telemetry_period_s: float = 0.3

    # Chế độ tự động
    clear_factor: float = 1.5     # hướng "thoáng" khi khoảng cách >= threshold * clear_factor
    turn_s: float = 0.45          # thời gian quay tại chỗ khi né
    backup_s: float = 0.5         # thời gian lùi khi cả hai bên bị chặn
    max_retries: int = 2          # số lần lùi + quét lại trước khi báo "blocked"

    # Servo / cảm biến
    side_angle: float = 70.0      # góc quét trái/phải
    servo_settle_s: float = 0.25
    max_distance_cm: float = 200.0

    # Camera OV5647 (luồng MJPEG qua HTTP, xem camera.py)
    camera_enabled: bool = field(default_factory=lambda: _env("CAMERA_ENABLED", True, bool))
    camera_port: int = field(default_factory=lambda: _env("CAMERA_PORT", 8001, int))
    camera_width: int = field(default_factory=lambda: _env("CAMERA_WIDTH", 640, int))
    camera_height: int = field(default_factory=lambda: _env("CAMERA_HEIGHT", 480, int))
    camera_fps: int = field(default_factory=lambda: _env("CAMERA_FPS", 15, int))
    camera_hflip: bool = field(default_factory=lambda: _env("CAMERA_HFLIP", False, bool))
    camera_vflip: bool = field(default_factory=lambda: _env("CAMERA_VFLIP", False, bool))
    camera_max_clients: int = field(default_factory=lambda: _env("CAMERA_MAX_CLIENTS", 3, int))
    camera_public_url: str = field(default_factory=lambda: _env("CAMERA_PUBLIC_URL", ""))  # để trống = tự đoán IP

    pins: Pins = field(default_factory=Pins)


SPEED_MIN, SPEED_MAX = 0.1, 1.0


def clamp_speed(s: float) -> float:
    return round(max(SPEED_MIN, min(SPEED_MAX, s)), 3)


def speed_to_duty(speed: float, min_duty: float, max_duty: float) -> float:
    """10% -> min_duty, 100% -> max_duty, tuyến tính ở giữa."""
    t = (clamp_speed(speed) - SPEED_MIN) / (SPEED_MAX - SPEED_MIN)
    return round(min_duty + t * (max_duty - min_duty), 3)


def load_config() -> Config:
    cfg = Config()
    cfg.speed = clamp_speed(cfg.speed)
    if not 0 < cfg.min_duty <= cfg.max_duty <= 1:
        raise ValueError("Cần 0 < MIN_DUTY <= MAX_DUTY <= 1")
    return cfg
