# Sơ đồ nối dây (việc 1)

> Bản nháp theo đề cương — Kiên cập nhật lại sau khi lắp thực tế và thêm ảnh/sơ đồ (Fritzing/draw.io) vào `docs/images/`.
> Số chân dưới đây là **GPIO BCM**, trùng với `car/smartcar/config.py`.

## Nguồn

```
3×18650 nối tiếp (~11.1V, đầy 12.6V)
   └── Công tắc
        ├── L298N  +12V  (nguồn motor)
        ├── LM2596 #1 → 5.1V → Pi Zero 2 W (chân 5V, pin 2/4)
        └── LM2596 #2 → 5V   → Servo SG90 + HC-SR04 VCC
Tất cả GND nối chung (pin, L298N, 2 LM2596, Pi).
```

⚠️ **Chỉnh LM2596 về 5.0–5.1V bằng đồng hồ TRƯỚC khi cắm Pi.**
⚠️ Motor vàng TT chịu 3–6V. L298N sụt ~2V nên motor nhận ~9–10V ở duty 100%. Vì vậy 100% trên website ứng với `MAX_DUTY=0.6` (≈ 5–6V), 10% ứng với `MIN_DUTY=0.3`. Chỉnh trong `car/.env`.
⚠️ Không lấy nguồn servo/motor từ chân 5V của Pi.

## L298N ↔ Pi

| L298N | Pi (BCM) | Pin vật lý | Ghi chú |
|---|---|---|---|
| ENA | GPIO12 | 32 | PWM trái — **tháo jumper ENA** |
| IN1 | GPIO5 | 29 | |
| IN2 | GPIO6 | 31 | |
| IN3 | GPIO20 | 38 | |
| IN4 | GPIO21 | 40 | |
| ENB | GPIO13 | 33 | PWM phải — **tháo jumper ENB** |
| GND | GND | 34 | |
| OUT1/OUT2 | — | — | 2 motor bên trái (nối song song) |
| OUT3/OUT4 | — | — | 2 motor bên phải (nối song song) |

Nếu xe chạy ngược chiều: đảo dây OUT của bên đó (hoặc đổi IN1↔IN2 trong config).

## HC-SR04

| HC-SR04 | Nối tới |
|---|---|
| VCC | 5V (LM2596 #2) |
| TRIG | GPIO23 (pin 16) |
| ECHO | **Mạch chia áp** → GPIO24 (pin 18) |
| GND | GND |

Chân ECHO ra 5V, GPIO Pi chỉ chịu 3.3V:

```
ECHO ──[ 1kΩ ]──┬── GPIO24
                │
              [ 2kΩ ]
                │
               GND        → 5V × 2/(1+2) ≈ 3.3V
```

## Camera OV5647

- Pi Zero 2 W dùng khe CSI **22 pin** nhỏ → cần cáp chuyển **15 pin → 22 pin** (có trong danh sách linh kiện).
- Tắt nguồn Pi trước khi cắm cáp. Mặt tiếp điểm kim loại của cáp úp **xuống phía mạch** ở cả hai đầu.
- Gắn camera ở đầu xe, phía trên HC-SR04 để servo không che. Nếu hình bị ngược, đặt `CAMERA_HFLIP=1` / `CAMERA_VFLIP=1` trong `car/.env`.

## Servo SG90

| SG90 | Nối tới |
|---|---|
| Nâu | GND |
| Đỏ | 5V (LM2596 #2) |
| Cam | GPIO18 (pin 12) |

Góc dương = quay cảm biến sang trái. Nếu ngược, đổi dấu `side_angle` trong config.
