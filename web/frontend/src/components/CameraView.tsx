import { useEffect, useRef, useState } from "react";
import type { CameraInfo, Telemetry } from "../types";

interface Props {
  camera: CameraInfo;
  carOnline: boolean;
  telemetry: Telemetry | null;
}

type ViewState = "off" | "loading" | "live" | "error";

const RETRY_MS = 2000;

/** Xe không biết IP của mình (vd. đang phát Wi-Fi) -> dùng địa chỉ điện thoại đang mở web. */
function fixHost(url: string): string {
  if (url.startsWith("data:")) return url;
  try {
    const u = new URL(url);
    if (["localhost", "127.0.0.1", "0.0.0.0"].includes(u.hostname)) u.hostname = location.hostname;
    return u.toString();
  } catch {
    return url;
  }
}

/** Khung xem camera OV5647 (luồng MJPEG từ Pi) với thông số đè lên hình. */
export function CameraView({ camera, carOnline, telemetry }: Props) {
  const boxRef = useRef<HTMLDivElement>(null);
  const [watching, setWatching] = useState(true);
  const [state, setState] = useState<ViewState>("loading");
  const [attempt, setAttempt] = useState(0); // đổi để tải lại luồng

  const available = carOnline && camera.enabled && !!camera.stream_url;
  const show = available && watching;

  // Mất hình -> thử lại sau 2s
  useEffect(() => {
    if (state !== "error" || !show) return;
    const t = setTimeout(() => {
      setState("loading");
      setAttempt((a) => a + 1);
    }, RETRY_MS);
    return () => clearTimeout(t);
  }, [state, show]);

  const streamUrl = camera.stream_url ? fixHost(camera.stream_url) : undefined;
  const src =
    show && streamUrl
      ? streamUrl.startsWith("data:")
        ? streamUrl
        : `${streamUrl}${streamUrl.includes("?") ? "&" : "?"}t=${attempt}`
      : undefined;

  // Đổi nguồn hình (bật lại, đổi địa chỉ) -> về trạng thái "đang tải".
  // Làm ngay trong render để không ghi đè "live" nếu ảnh tải xong quá nhanh.
  const [prevSrc, setPrevSrc] = useState(src);
  if (src !== prevSrc) {
    setPrevSrc(src);
    if (src) setState("loading");
  }
  const view: ViewState = show ? state : "off";

  const toggleFullscreen = async () => {
    const el = boxRef.current;
    if (!el) return;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await el.requestFullscreen();
    } catch {
      /* trình duyệt không cho phép toàn màn hình */
    }
  };

  const d = telemetry?.distance_cm ?? null;
  const near = telemetry != null && d != null && d < telemetry.threshold_cm;
  const ratio = camera.width && camera.height ? `${camera.width} / ${camera.height}` : "4 / 3";

  let placeholder: string | null = null;
  if (!carOnline) placeholder = "Xe chưa kết nối";
  else if (!camera.enabled) placeholder = "Xe không bật camera";
  else if (!watching) placeholder = "Đã tắt hình để tiết kiệm băng thông";
  else if (view === "loading") placeholder = "Đang tải hình…";
  else if (view === "error") placeholder = "Mất hình — đang thử lại…";

  return (
    <section className="card camera-card">
      <div ref={boxRef} className={near ? "camera-box near" : "camera-box"} style={{ aspectRatio: ratio }}>
        {src && (
          <img
            key={attempt}
            className={view === "live" ? "camera-img" : "camera-img hidden"}
            src={src}
            alt="Hình từ camera trên xe"
            onLoad={() => setState("live")}
            onError={() => setState("error")}
            draggable={false}
          />
        )}

        {placeholder && <div className="camera-placeholder">{placeholder}</div>}

        {view === "live" && (
          <>
            <span className="hud hud-tl">
              <span className="rec-dot" /> LIVE
            </span>
            <span className="hud hud-tr">{telemetry?.mode === "auto" ? "TỰ ĐỘNG" : "THỦ CÔNG"}</span>
            <span className={near ? "hud hud-bl warn" : "hud hud-bl"}>{d == null ? "--" : d.toFixed(0)} cm</span>
            {camera.fps && <span className="hud hud-br">{camera.fps} fps</span>}
          </>
        )}
      </div>

      <div className="camera-actions">
        <button onClick={() => setWatching((w) => !w)} disabled={!available}>
          {watching ? "Tắt hình" : "Bật hình"}
        </button>
        <button onClick={toggleFullscreen} disabled={view !== "live"}>
          Toàn màn hình
        </button>
        {camera.snapshot_url && (
          <a className="button-link" href={fixHost(camera.snapshot_url)} target="_blank" rel="noreferrer">
            Chụp ảnh
          </a>
        )}
      </div>
    </section>
  );
}
