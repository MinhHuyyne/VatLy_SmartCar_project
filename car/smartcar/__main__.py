"""Chạy:  python -m smartcar        (trên Pi)
        SMARTCAR_SIM=1 python -m smartcar   (giả lập trên laptop)
"""
import logging

from .config import load_config
from .controller import CarController
from .mqtt_link import MqttLink


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = load_config()

    if cfg.sim:
        from . import sim as hw
        logging.info("Chạy ở chế độ GIẢ LẬP (không dùng GPIO)")
    else:
        from . import hardware as hw
    drive, scanner = hw.build(cfg)

    link = MqttLink(cfg)

    camera = None
    if cfg.camera_enabled and not cfg.sim:
        try:
            from .camera import CameraStreamer
            camera = CameraStreamer(cfg)
            link.camera_info = camera.start()
        except Exception:  # thiếu camera / chưa cắm cáp: xe vẫn chạy bình thường
            logging.exception("Không bật được camera — tiếp tục chạy không có camera")
            camera = None

    ctrl = CarController(drive, scanner, cfg, publish=link.publish)
    link.on_command = ctrl.submit
    link.on_lost = ctrl.on_link_lost
    link.start()
    logging.info("Xe %s -> MQTT %s:%s", cfg.car_id, cfg.mqtt_host, cfg.mqtt_port)

    try:
        ctrl.run()
    except KeyboardInterrupt:
        pass
    finally:
        ctrl.stop()
        link.stop()
        if camera:
            camera.stop()


if __name__ == "__main__":
    main()
