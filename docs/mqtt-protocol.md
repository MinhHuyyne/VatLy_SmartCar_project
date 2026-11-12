# Bảng lệnh và dữ liệu MQTT (việc 2)

Tiền tố topic: `smartcar/<car_id>` (mặc định `car01`). Mọi payload là JSON UTF-8, trừ `status`.

| Topic | Chiều | QoS | Retain | Nội dung |
|---|---|---|---|---|
| `smartcar/car01/cmd` | Web → Xe | 1 (heartbeat: 0) | không | Lệnh điều khiển |
| `smartcar/car01/ack` | Xe → Web | 1 | không | Phản hồi xác nhận cho từng lệnh |
| `smartcar/car01/telemetry` | Xe → Web | 0 | không | Khoảng cách, trạng thái — mỗi 300 ms |
| `smartcar/car01/event` | Xe → Web | 1 | không | Cảnh báo / lỗi |
| `smartcar/car01/status` | Xe → Web | 1 | **có** | `online` / `offline` (Last Will) |
| `smartcar/car01/camera` | Xe → Web | 1 | **có** | Địa chỉ luồng camera |

## Lệnh (`cmd`)

Mọi lệnh có `type` và `id` (backend tự sinh nếu thiếu). Xe trả lại `ack` cùng `id`.

| `type` | Trường thêm | Ví dụ |
|---|---|---|
| `move` | `dir`: `forward` \| `backward` \| `left` \| `right` \| `stop` | `{"type":"move","dir":"forward","id":"a1"}` |
| `mode` | `mode`: `manual` \| `auto` | `{"type":"mode","mode":"auto","id":"a2"}` |
| `config` | `threshold_cm` (5–150), `speed` (0.1–1.0 = 10–100%) | `{"type":"config","threshold_cm":30,"id":"a3"}` |
| `heartbeat` | — | `{"type":"heartbeat"}` (website gửi mỗi 500 ms) |

**Tốc độ:** `speed` là phần trăm người dùng chọn, không phải điện áp. Xe quy đổi tuyến tính sang duty PWM:
10% → `MIN_DUTY` (mặc định 0.3, chậm nhất mà motor vẫn quay), 100% → `MAX_DUTY` (mặc định 0.6, bảo vệ motor 3–6V).
Hai giá trị này chỉnh trong `car/.env` sau khi thử trên xe thật.

## Phản hồi (`ack`)

```json
{"id":"a1","ok":true,"mode":"manual","state":"moving_forward","direction":"forward",
 "distance_cm":84.2,"threshold_cm":25,"speed":0.5,"ts":1731400000.1}
```

Khi `ok=false`, có thêm `error`:

| `error` | Ý nghĩa |
|---|---|
| `auto_mode` | Đang ở chế độ tự động, bỏ qua lệnh hướng thủ công |
| `obstacle` | Vật cản gần hơn ngưỡng, không cho tiến |
| `unknown_command` | `type` không hợp lệ |
| `bad_request: ...` | Thiếu trường / giá trị sai |

## Telemetry

Giống phần trạng thái trong `ack` (không có `id`, `ok`).
Giá trị `state`: `idle`, `moving_<dir>`, `cruising`, `scanning`, `turning_left`, `turning_right`, `reversing`, `blocked`.

## Event

```json
{"level":"warn","code":"obstacle_stop","msg":"Vật cản cách 18.0 cm — xe tự dừng.","ts":...}
```

| `code` | `level` | Khi nào |
|---|---|---|
| `obstacle_stop` | warn | Thủ công: đang tiến mà gặp vật cản |
| `heartbeat_lost` | warn | Không nhận heartbeat quá `HEARTBEAT_TIMEOUT_S` → dừng |
| `blocked` | error | Tự động: lùi + quét lại `max_retries` lần vẫn bị chặn → dừng |

## Camera

Video **không** đi qua MQTT. Pi phát MJPEG qua HTTP, MQTT chỉ báo địa chỉ để website tự hiển thị:

```json
{"enabled":true,"stream_url":"http://192.168.1.20:8001/stream.mjpg",
 "snapshot_url":"http://192.168.1.20:8001/snapshot.jpg","width":640,"height":480,"fps":15}
```

Khi xe tắt đúng cách hoặc không có camera: `{"enabled":false}`.

## Thử nhanh bằng MQTT client

```bash
mosquitto_sub -h <broker> -t 'smartcar/car01/#' -v
mosquitto_pub -h <broker> -t smartcar/car01/cmd -m '{"type":"move","dir":"forward","id":"t1"}'
mosquitto_pub -h <broker> -t smartcar/car01/cmd -m '{"type":"move","dir":"stop","id":"t2"}'
```
