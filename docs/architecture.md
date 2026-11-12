# Kiến trúc hệ thống (việc 2)

```
 Điện thoại / máy tính
 ┌────────────────────┐   WebSocket /ws   ┌───────────────┐   MQTT   ┌──────────────┐   MQTT   ┌─────────────────────────┐
 │ web/frontend       │ ────────────────▶ │ web/backend   │ ───────▶ │  Mosquitto   │ ───────▶ │ Raspberry Pi Zero 2 W   │
 │ (React + TS)       │ ◀──────────────── │ FastAPI       │ ◀─────── │  broker      │ ◀─────── │ car/smartcar            │
 └────────────────────┘  ack/telemetry    └───────────────┘          └──────────────┘          └──────────┬──────────────┘
                                                                                                         GPIO
                                                                         ┌───────────────┬──────────────┼──────────────┐
                                                                     L298N + 4 motor   HC-SR04        SG90 servo
```

## Phần mềm trên xe (`car/smartcar`)

| Module | Vai trò | Việc |
|---|---|---|
| `hardware.py` | `DriveTrain` (L298N), `Ultrasonic` (HC-SR04), `Scanner` (servo + cảm biến) | 5, 6 |
| `sim.py` | Phần cứng giả lập để chạy trên laptop | — |
| `autopilot.py` | Thuật toán tránh vật cản: đo → dừng → quét → chọn hướng → lùi/báo chặn | 9 |
| `controller.py` | Hàng đợi lệnh, chuyển chế độ, dừng an toàn, gửi ack/telemetry | 10, 12 |
| `mqtt_link.py` | Kết nối broker, LWT `offline`, tự kết nối lại | 7 |
| `camera.py` | Phát hình OV5647 dạng MJPEG qua HTTP (cổng 8001) | — |
| `protocol.py` | Topic + enum lệnh dùng chung | 2 |

## Camera

```
OV5647 ──CSI──▶ Pi (Picamera2 + mã hoá MJPEG phần cứng) ──HTTP :8001/stream.mjpg──▶ <img> trên website
                 └── MQTT topic `camera` (retained): báo địa chỉ luồng cho website
```

Video đi thẳng từ Pi tới trình duyệt, không qua MQTT/backend, để không làm chậm lệnh điều khiển.
Lưu ý: nếu website mở bằng `https://` thì trình duyệt sẽ chặn luồng `http://` của Pi — khi demo hãy dùng `http://` trong mạng LAN.

**Nguyên tắc:** mọi lệnh MQTT được đẩy vào hàng đợi và xử lý trong **một vòng lặp chính duy nhất** (~20 Hz), vì vậy chế độ thủ công và tự động không bao giờ điều khiển motor cùng lúc. Trong lúc tự động đang quay/lùi, nếu có lệnh mới thì thao tác bị cắt ngắn để xử lý lệnh ngay.

## Dừng an toàn

| Tình huống | Cách phát hiện | Hành động |
|---|---|---|
| Quá gần vật cản (thủ công) | `distance < threshold` khi đang tiến | Dừng + event `obstacle_stop` |
| Website đóng / điện thoại mất mạng | Không có heartbeat > 1.5 s | Dừng + event `heartbeat_lost` |
| Xe mất kết nối broker | `on_disconnect` của paho | Dừng; broker phát `offline` (LWT) |
| Bị chặn mọi hướng (tự động) | Lùi + quét lại quá `max_retries` | Dừng + event `blocked` |
| Đổi chế độ | Lệnh `mode` | Luôn dừng trước |

## Triển khai

- **Phát triển:** broker + backend chạy trên laptop bằng `docker compose`; xe (thật hoặc giả lập) trỏ `MQTT_HOST` về IP laptop.
- **Demo:** có thể chạy cả Mosquitto + backend ngay trên Pi (`sudo apt install mosquitto`), điện thoại vào `http://<IP-Pi>:8000`.
