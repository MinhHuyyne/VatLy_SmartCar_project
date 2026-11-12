// Kiểu dữ liệu theo docs/mqtt-protocol.md — giữ đồng bộ với car/smartcar/protocol.py

export type Mode = "manual" | "auto";
export type Direction = "forward" | "backward" | "left" | "right" | "stop";

export type Command =
  | { type: "move"; dir: Direction }
  | { type: "mode"; mode: Mode }
  | { type: "config"; threshold_cm?: number; speed?: number }
  | { type: "heartbeat" };

export interface Telemetry {
  mode: Mode;
  state: string;
  direction: Direction;
  distance_cm: number | null;
  threshold_cm: number;
  speed: number;
  ts: number;
}

export interface Ack extends Telemetry {
  id: string;
  ok: boolean;
  error?: string;
}

export interface CarEvent {
  level: "info" | "warn" | "error";
  code: string;
  msg: string;
  ts: number;
}

export type CarStatus = "online" | "offline" | "unknown";

/** Thông tin luồng camera xe gửi lên topic `camera` (retained) */
export interface CameraInfo {
  enabled: boolean;
  stream_url?: string;
  snapshot_url?: string;
  width?: number;
  height?: number;
  fps?: number;
}

/** Tin nhắn backend gửi qua WebSocket */
export type ServerMessage =
  | {
      kind: "hello";
      data: {
        car_id: string;
        broker_connected: boolean;
        status: CarStatus;
        telemetry: Telemetry | null;
        camera?: CameraInfo;
      };
    }
  | { kind: "broker"; data: { connected: boolean } }
  | { kind: "status"; data: CarStatus }
  | { kind: "telemetry"; data: Telemetry }
  | { kind: "camera"; data: CameraInfo }
  | { kind: "ack"; data: Ack }
  | { kind: "event"; data: CarEvent }
  | { kind: "sent"; data: { id: string } };

export interface LogEntry {
  id: number;
  time: string;
  msg: string;
  level: "info" | "warn" | "error";
}

export const DIR_LABEL: Record<Direction, string> = {
  forward: "Tiến",
  backward: "Lùi",
  left: "Trái",
  right: "Phải",
  stop: "Dừng",
};
