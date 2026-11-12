# Cài đặt Raspberry Pi Zero 2 W (việc 4)

1. **Raspberry Pi Imager** → *Raspberry Pi OS Lite (64-bit)*. Trong phần tuỳ chỉnh: đặt hostname `smartcar`, user `pi`, Wi-Fi, bật SSH.
2. Cắm nguồn, chờ ~1 phút: `ssh pi@smartcar.local`
3. Cập nhật và cài gói:
   ```bash
   sudo apt update && sudo apt full-upgrade -y
   sudo apt install -y git python3-venv python3-lgpio python3-picamera2 mosquitto-clients
   ```
4. Lấy code:
   ```bash
   git clone https://github.com/<user>/VatLy_SmartCar.git ~/VatLy_SmartCar
   cd ~/VatLy_SmartCar/car
   python3 -m venv --system-site-packages .venv
   .venv/bin/pip install -r requirements.txt
   cp .env.example .env && nano .env      # sửa MQTT_HOST
   ```
5. Chạy thử: `.venv/bin/python -m smartcar`
6. Chạy tự động khi bật xe:
   ```bash
   sudo cp deploy/smartcar.service /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now smartcar
   journalctl -u smartcar -f      # xem log
   ```

**(Tuỳ chọn) chạy broker ngay trên Pi:** `sudo apt install -y mosquitto` rồi thêm `listener 1883` + `allow_anonymous true` vào `/etc/mosquitto/conf.d/smartcar.conf`, `sudo systemctl restart mosquitto`.

**Kiểm tra camera** (đã cắm cáp CSI, khởi động lại Pi):
```bash
rpicam-hello --list-cameras          # phải thấy ov5647
rpicam-still -o test.jpg             # chụp thử
```
Nếu không thấy camera: thêm `dtoverlay=ov5647` vào `/boot/firmware/config.txt`, khởi động lại.
Khi xe chạy, xem hình tại `http://smartcar.local:8001/stream.mjpg`.

**Kiểm tra từng linh kiện** (trước khi chạy cả chương trình):
```bash
.venv/bin/python -c "from gpiozero import DistanceSensor as D; import time; s=D(echo=24,trigger=23); [print(round(s.distance*100,1)) or time.sleep(.3) for _ in range(10)]"
```
