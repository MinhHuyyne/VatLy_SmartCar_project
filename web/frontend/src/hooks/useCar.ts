import { useCallback, useEffect, useRef, useState } from "react";
import type { CameraInfo, CarStatus, Command, LogEntry, ServerMessage, Telemetry } from "../types";

const HEARTBEAT_MS = 500;
const ACK_TIMEOUT_MS = 2000;
const RECONNECT_MS = 1500;
const MAX_LOG = 50;

interface Pending {
  label: string;
  timer: ReturnType<typeof setTimeout>;
}

/** Quản lý kết nối WebSocket tới backend, heartbeat và chờ phản hồi xác nhận từ xe. */
export function useCar() {
  const wsRef = useRef<WebSocket | null>(null);
  const pendingRef = useRef(new Map<string, Pending>());
  const logIdRef = useRef(0);

  const [webConnected, setWebConnected] = useState(false);
  const [brokerConnected, setBrokerConnected] = useState<boolean | null>(null);
  const [carStatus, setCarStatus] = useState<CarStatus>("unknown");
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [camera, setCamera] = useState<CameraInfo>({ enabled: false });

  const log = useCallback((msg: string, level: LogEntry["level"] = "info") => {
    const entry: LogEntry = { id: ++logIdRef.current, time: new Date().toLocaleTimeString(), msg, level };
    setLogs((prev) => [entry, ...prev].slice(0, MAX_LOG));
  }, []);

  const handle = useCallback(
    (m: ServerMessage) => {
      switch (m.kind) {
        case "hello":
          setBrokerConnected(m.data.broker_connected);
          setCarStatus(m.data.status);
          if (m.data.telemetry) setTelemetry(m.data.telemetry);
          if (m.data.camera) setCamera(m.data.camera);
          break;
        case "broker":
          setBrokerConnected(m.data.connected);
          break;
        case "status":
          setCarStatus(m.data);
          log(`Xe ${m.data}`, m.data === "online" ? "info" : "warn");
          break;
        case "telemetry":
          setTelemetry(m.data);
          break;
        case "camera":
          setCamera(m.data);
          break;
        case "ack": {
          const { id, ok, error, ...snapshot } = m.data;
          const p = pendingRef.current.get(id);
          if (p) {
            clearTimeout(p.timer);
            pendingRef.current.delete(id);
            // Chỉ báo "đã thực hiện" khi có xác nhận từ xe
            log(ok ? `✓ ${p.label}` : `✗ ${p.label} (${error})`, ok ? "info" : "warn");
          }
          setTelemetry(snapshot);
          break;
        }
        case "event":
          log(m.data.msg, m.data.level);
          break;
        case "sent":
          break;
      }
    },
    [log],
  );

  // Kết nối + tự kết nối lại
  useEffect(() => {
    let closed = false;
    let retry: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${proto}://${location.host}/ws`);
      wsRef.current = ws;
      ws.onopen = () => {
        setWebConnected(true);
        log("Đã kết nối backend");
      };
      ws.onclose = () => {
        if (wsRef.current !== ws) return; // socket cũ (vd. StrictMode mount 2 lần)
        setWebConnected(false);
        setBrokerConnected(null);
        setCarStatus("unknown");
        if (!closed) retry = setTimeout(connect, RECONNECT_MS);
      };
      ws.onmessage = (e: MessageEvent<string>) => handle(JSON.parse(e.data) as ServerMessage);
    };
    connect();

    return () => {
      closed = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, [handle, log]);

  // Heartbeat: xe tự dừng nếu không nhận được trong 1.5 s
  useEffect(() => {
    const t = setInterval(() => {
      const ws = wsRef.current;
      if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "heartbeat" }));
    }, HEARTBEAT_MS);
    return () => clearInterval(t);
  }, []);

  /** Gửi lệnh; nếu có label thì chờ ack và ghi log kết quả. */
  const send = useCallback(
    (cmd: Command, label?: string) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        log("Chưa kết nối backend", "error");
        return;
      }
      const id = Math.random().toString(36).slice(2, 10);
      ws.send(JSON.stringify({ ...cmd, id }));
      if (label) {
        const timer = setTimeout(() => {
          pendingRef.current.delete(id);
          log(`${label}: xe không phản hồi`, "error");
        }, ACK_TIMEOUT_MS);
        pendingRef.current.set(id, { label, timer });
      }
    },
    [log],
  );

  return { webConnected, brokerConnected, carStatus, telemetry, camera, logs, send };
}
