# Kế hoạch kiểm thử (việc 13, 14)

Ghi kết quả thực tế vào cột cuối; lỗi tìm thấy thì mở Issue và ghi số Issue.

## A. Thủ công & mất kết nối (Huy — việc 13)

| # | Kịch bản | Mong đợi | Kết quả |
|---|---|---|---|
| A1 | Giữ ▲ / ▼ / ◀ / ▶ rồi thả | Xe chạy đúng hướng, thả ra dừng; log hiện ✓ | |
| A2 | Bấm ▲ khi vật cản < ngưỡng | Xe không chạy, log `obstacle` | |
| A3 | Đang tiến, đặt vật cản phía trước | Xe tự dừng, event `obstacle_stop` | |
| A4 | Đang chạy, tắt Wi-Fi điện thoại | Xe dừng trong ≤ 1.5 s | |
| A5 | Đang chạy, tắt broker | Xe dừng; web hiện MQTT đỏ | |
| A6 | Rút nguồn Pi | Web hiện Xe đỏ (offline) | |
| A7 | Đang chạy thủ công → bấm Tự động | Xe dừng trước rồi mới tự chạy | |
| A8 | Đổi ngưỡng 25 → 50 cm | Xe dừng xa hơn | |
| A8b | Kéo tốc độ 10% → 100% | 10% xe vẫn bò được; 100% nhanh nhất, motor không nóng bất thường | |
| A9 | Độ trễ bấm nút → xe chạy | < 300 ms | |

## B. Camera

| # | Kịch bản | Mong đợi | Kết quả |
|---|---|---|---|
| B1 | Mở website khi xe chạy | Khung camera hiện hình, có HUD khoảng cách | |
| B2 | Độ trễ hình (vẫy tay trước camera) | < 500 ms | |
| B3 | Tắt / bật hình | Ngừng / tiếp tục nhận hình | |
| B4 | Rút nguồn Pi rồi cắm lại | Web báo mất hình, có hình lại khi xe online | |
| B5 | 2 điện thoại cùng xem | Cả hai có hình, xe vẫn điều khiển mượt | |
| B6 | Khởi động xe khi chưa cắm camera | Xe vẫn chạy, web báo "Xe không bật camera" | |

## C. Tự động (Kiên — việc 14)

| # | Kịch bản | Mong đợi | Kết quả |
|---|---|---|---|
| C1 | Đường thẳng không vật cản | Đi thẳng | |
| C2 | Vật cản chính diện, bên phải trống | Dừng, quét, rẽ phải | |
| C3 | Vật cản chính diện, bên trái trống | Rẽ trái | |
| C4 | Ngõ cụt 3 mặt | Lùi, quét lại; sau 2 lần báo `blocked` | |
| C5 | Vật cản mỏng (chân ghế) | Ghi nhận khả năng phát hiện | |
| C6 | Vật mềm (vải, gối) | Ghi nhận — siêu âm có thể đo sai | |
| C7 | Đang tự động → bấm Thủ công | Xe dừng ngay, chờ lệnh | |
| C8 | Các tốc độ 30% / 45% / 60% | Chọn tốc độ dừng kịp trước vật cản | |

## D. Test tự động (không cần xe)

```bash
cd car && pytest -q
```
