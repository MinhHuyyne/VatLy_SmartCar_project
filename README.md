# VatLy_SmartCar — Xe robot điều khiển thông minh

Đồ án cuối kỳ môn **Vật lý cho Công nghệ Thông tin** — lớp 24C11, nhóm 03, Trường ĐH KHTN – ĐHQG TP.HCM, HK I 2026–2027.

| MSSV | Thành viên | Phụ trách chính |
|---|---|---|
| 24127194 | Hoàng Trung Kiên | Phần cứng, điều khiển motor, cảm biến, chế độ tự động |
| 24127403 | Trần Quang Minh Huy | Kiến trúc, MQTT, backend + website, chế độ thủ công |

GVHD: ThS. Lê Quốc Hòa, ThS. Đặng Hoài Thương, ThS. Cao Xuân Nam.

## Giới thiệu

Xe robot 4 bánh dùng **Raspberry Pi Zero 2 W**, driver **L298N**, cảm biến siêu âm **HC-SR04** gắn trên servo **SG90**. Hai chế độ:

- **Thủ công** — điều khiển tiến / lùi / trái / phải / dừng từ website trên điện thoại.
- **Camera** — xem hình trực tiếp từ camera OV5647 trên website, kèm khoảng cách và chế độ đè lên hình.
- **Tự động** — tự đi thẳng, gặp vật cản thì dừng, quét trái–phải, chọn hướng thoáng; bị chặn thì lùi và quét lại, vẫn không có đường thì dừng và báo lên web.

Lệnh và trạng thái truyền qua **MQTT**: `Website ⇄ Backend ⇄ Mosquitto ⇄ Raspberry Pi`.

## Cấu trúc repo

```
VatLy_SmartCar/
├── car/                     # Chạy trên Raspberry Pi (Python)
│   ├── smartcar/
│   │   ├── hardware.py      # L298N, HC-SR04, servo (gpiozero)
│   │   ├── sim.py           # phần cứng giả lập để chạy trên laptop
│   │   ├── autopilot.py     # thuật toán tránh vật cản
│   │   ├── controller.py    # điều phối chế độ + dừng an toàn
│   │   ├── camera.py        # phát hình OV5647 (MJPEG qua HTTP)
│   │   ├── mqtt_link.py     # kết nối MQTT
│   │   ├── protocol.py      # topic & lệnh
│   │   └── config.py        # chân GPIO, ngưỡng, tốc độ
│   ├── tests/               # pytest (không cần phần cứng)
│   └── deploy/smartcar.service
├── web/
│   ├── backend/             # FastAPI: WebSocket <-> MQTT
│   └── frontend/            # React + TypeScript (Vite) + CSS, tối ưu cho điện thoại
│       └── src/
│           ├── App.tsx
│           ├── components/  # CameraView, StatusBar, TelemetryCard, ModeSwitch, DPad, SettingsCard, EventLog
│           ├── hooks/useCar.ts  # WebSocket, heartbeat, chờ ack
│           ├── types.ts     # kiểu dữ liệu theo bảng lệnh MQTT
│           └── styles.css
├── broker/mosquitto.conf
├── docs/                    # kiến trúc, bảng lệnh MQTT, nối dây, cài Pi, kiểm thử
├── hardware/bom.md          # linh kiện & dự toán
└── docker-compose.yml       # broker + backend trên laptop
```

## Chạy nhanh (không cần xe)

```bash
# 1. Broker + backend
docker compose up --build              # mở http://localhost:8000

# 2. Xe giả lập (terminal khác)
cd car
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install paho-mqtt
SMARTCAR_SIM=1 MQTT_HOST=localhost python -m smartcar  # Windows PowerShell: $env:SMARTCAR_SIM=1; python -m smartcar
```

Không dùng Docker? Cài [Mosquitto](https://mosquitto.org/download/) và [Node.js 20+](https://nodejs.org/) rồi:
```bash
# Backend
cd web/backend && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend khi đang code (hot reload, tự proxy /ws sang backend :8000)
cd web/frontend && npm install && npm run dev      # mở http://localhost:5173

# Frontend bản build để backend phục vụ ở :8000
cd web/frontend && npm run build                    # tạo web/frontend/dist
```

Điện thoại cùng Wi-Fi: mở `http://<IP-laptop>:8000` (hoặc `:5173` khi chạy `npm run dev`). Trên máy tính có thể dùng phím **W A S D**, **Space** = dừng.

## Điều khiển bằng điện thoại

Không cần cài app — mở web bằng trình duyệt điện thoại, có thể *Thêm vào màn hình chính* để dùng như app. Xoay ngang để vào chế độ lái (camera lớn, nút bên phải).

- **Cùng Wi-Fi:** mở địa chỉ backend in ra khi khởi động, vd `http://192.168.1.10:8000`.
- **Không có Wi-Fi (demo):** Pi tự phát Wi-Fi `SmartCar`, điện thoại vào `http://10.42.0.1:8000`.

Chi tiết: [docs/phone.md](docs/phone.md).

## Chạy trên xe thật

Xem [docs/setup-raspberry-pi.md](docs/setup-raspberry-pi.md) và [docs/wiring.md](docs/wiring.md).
⚠️ Chân ECHO của HC-SR04 phải qua mạch chia áp 5V → 3.3V.

## Test

```bash
cd car && pip install pytest && pytest -q        # logic xe
cd web/frontend && npm run typecheck               # kiểm tra kiểu TypeScript
```

GitHub Actions tự chạy test mỗi lần push (`.github/workflows/ci.yml`).

## Tài liệu

- [Điều khiển bằng điện thoại](docs/phone.md)
- [Kiến trúc hệ thống](docs/architecture.md)
- [Bảng lệnh & dữ liệu MQTT](docs/mqtt-protocol.md)
- [Sơ đồ nối dây](docs/wiring.md)
- [Kế hoạch kiểm thử](docs/test-plan.md)
- [Linh kiện & dự toán](hardware/bom.md)

## Kế hoạch & phân công (6 tuần)

Mỗi việc nên là 1 GitHub Issue (dùng template *Đầu việc*), gắn milestone theo tuần.

| # | Việc | Tuần | Người | Thư mục |
|---|---|---|---|---|
| 1 | Sơ đồ nối dây | 1 | Kiên | `docs/wiring.md` |
| 2 | Kiến trúc & bảng lệnh MQTT | 1 | Huy | `docs/architecture.md`, `docs/mqtt-protocol.md` |
| 3 | Lắp ráp khung xe & đấu nguồn | 1 | Kiên | `docs/images/` |
| 4 | Cài Raspberry Pi Zero 2 W | 1 | Huy | `docs/setup-raspberry-pi.md` |
| 5 | Điều khiển động cơ | 2 | Kiên | `car/smartcar/hardware.py` |
| 6 | Đo khoảng cách & quét hướng | 2 | Kiên | `car/smartcar/hardware.py` |
| 7 | MQTT broker & kết nối xe | 2 | Huy | `broker/`, `car/smartcar/mqtt_link.py` |
| 8 | Backend & giao diện website | 2–3 | Huy | `web/` |
| 9 | Chế độ tự động | 2–3 | Kiên | `car/smartcar/autopilot.py` |
| 10 | Chế độ thủ công & chuyển chế độ | 2–3 | Huy | `car/smartcar/controller.py` |
| 11 | Tích hợp phía website | 3–4 | Huy | `web/` |
| 12 | Tích hợp phía xe | 3–4 | Kiên | `car/` |
| 13 | Kiểm thử thủ công & mất kết nối | 4–5 | Huy | `docs/test-plan.md` |
| 14 | Kiểm thử tự động | 4–5 | Kiên | `docs/test-plan.md` |
| 15 | Báo cáo phần xe & dự toán | 6 | Kiên | `report/` |
| 16 | Báo cáo phần website & MQTT | 6 | Huy | `report/` |
| 17 | Tổng hợp đề cương | 1 | Kiên | `report/` |
| 18 | Bản vẽ phác thảo | 1 | Huy | `docs/images/` |

## Quy ước làm việc

- Nhánh `main` luôn chạy được. Làm việc trên nhánh riêng: `feat/9-autopilot`, `fix/13-heartbeat`… rồi mở Pull Request, người còn lại review.
- Commit message ngắn, có số việc: `feat(car): quét trái phải bằng servo (#6)`.
- Không commit file `.env`, mật khẩu Wi-Fi/MQTT.
- Sửa `car/smartcar/protocol.py` thì sửa luôn `web/backend/app/protocol.py` và `docs/mqtt-protocol.md`.
