# Điều khiển bằng điện thoại

Giao diện điều khiển là một trang web, nên **không cần cài app**: mở bằng Chrome (Android) hoặc Safari (iPhone) là dùng được. Có 2 cách cho điện thoại kết nối tới xe.

| | Cách A — Cùng Wi-Fi | Cách B — Pi tự phát Wi-Fi |
|---|---|---|
| Cần router / Wi-Fi có sẵn | Có | **Không** |
| Broker + backend chạy ở | Laptop | Raspberry Pi |
| Hợp với | Lúc code, thử nghiệm | **Demo trên lớp**, ngoài trời |
| Điện thoại mở | `http://<IP-laptop>:8000` | `http://10.42.0.1:8000` |

---

## Cách A — Điện thoại, laptop và xe cùng một Wi-Fi

```
Điện thoại ──┐
Laptop (broker + backend) ──┼── Router Wi-Fi
Xe (Pi) ─────┘
```

1. Laptop: `docker compose up --build` (hoặc chạy Mosquitto + `uvicorn` như README).
2. Log của backend in ra địa chỉ, ví dụ:
   ```
   📱 Mở trên điện thoại (cùng Wi-Fi): http://192.168.1.10:8000
   ```
3. Trong `car/.env` trên Pi: `MQTT_HOST=192.168.1.10` (IP laptop), khởi động lại `smartcar`.
4. Điện thoại vào đúng Wi-Fi đó, mở địa chỉ ở bước 2.

**Không vào được?**
- Windows Firewall chặn: lần đầu chạy, bấm *Allow* cho Python/Docker; hoặc mở cổng 8000 và 1883.
- Wi-Fi trường/quán cà phê thường **chặn các máy nói chuyện với nhau** (client isolation) → dùng Cách B, hoặc phát Wi-Fi từ điện thoại/laptop.

---

## Cách B — Raspberry Pi tự phát Wi-Fi (khuyên dùng khi demo)

Mọi thứ chạy trên xe; điện thoại kết nối thẳng vào Wi-Fi của xe.

```
Điện thoại ──Wi-Fi "SmartCar"──▶ Pi Zero 2 W  [Mosquitto + backend + smartcar + camera]
```

### Cài một lần (Pi cần Internet lúc cài)

```bash
# 1. Broker MQTT trên Pi
sudo apt install -y mosquitto
echo -e "listener 1883\nallow_anonymous true" | sudo tee /etc/mosquitto/conf.d/smartcar.conf
sudo systemctl restart mosquitto

# 2. Backend
cd ~/VatLy_SmartCar/web/backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

3. **Giao diện**: Pi Zero 2 W yếu, nên build trên laptop rồi chép sang:
   ```bash
   # trên laptop
   cd web/frontend && npm install && npm run build
   scp -r dist pi@smartcar.local:~/VatLy_SmartCar/web/frontend/
   ```

4. Chạy tự động khi bật xe:
   ```bash
   cd ~/VatLy_SmartCar/car
   sudo cp deploy/smartcar-web.service /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now smartcar-web
   ```
   Trong `car/.env`: `MQTT_HOST=localhost`.

### Bật Wi-Fi của xe

```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid SmartCar password smartcar123
sudo nmcli connection modify Hotspot connection.autoconnect yes connection.autoconnect-priority 100
```

Từ giờ mỗi lần bật xe, Pi phát Wi-Fi **SmartCar**. Điện thoại kết nối vào rồi mở **http://10.42.0.1:8000**.

> ⚠️ Khi Pi đang phát Wi-Fi thì nó **không còn vào mạng nhà/Internet** (Pi Zero 2 W chỉ có 1 card Wi-Fi), và SSH phải đi qua Wi-Fi SmartCar (`ssh pi@10.42.0.1`).
> Quay lại Wi-Fi nhà: `sudo nmcli connection down Hotspot && sudo nmcli connection up "<tên Wi-Fi nhà>"`.

Điện thoại có thể báo "Wi-Fi không có Internet" — chọn **Vẫn kết nối / Keep connection**, nếu không điện thoại sẽ tự chuyển sang 4G và không vào được xe.

---

## Dùng như một app

- **Android (Chrome):** menu ⋮ → *Thêm vào màn hình chính* / *Cài đặt ứng dụng*.
- **iPhone (Safari):** nút Chia sẻ → *Thêm vào MH chính*.

Mở từ icon **Smart Car** → giao diện toàn màn hình, không có thanh địa chỉ.

## Mẹo khi lái

- **Xoay ngang điện thoại** → chế độ lái: camera chiếm gần hết màn hình, nút điều khiển ở bên phải.
- Giữ nút để chạy, thả ra xe dừng. Trượt ngón tay ra khỏi nút vẫn giữ lệnh cho tới khi nhấc tay.
- Android rung nhẹ mỗi lần bấm (iPhone không hỗ trợ rung trên web).
- Màn hình được giữ sáng khi đang kết nối.
- Nếu tắt màn hình / chuyển app, website ngừng gửi heartbeat → xe **tự dừng sau 1,5 giây**.
