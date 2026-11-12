import { useCallback } from "react";
import { CameraView } from "./components/CameraView";
import { DPad } from "./components/DPad";
import { EventLog } from "./components/EventLog";
import { ModeSwitch } from "./components/ModeSwitch";
import { SettingsCard } from "./components/SettingsCard";
import { StatusBar } from "./components/StatusBar";
import { TelemetryCard } from "./components/TelemetryCard";
import { useCar } from "./hooks/useCar";
import { useWakeLock } from "./hooks/useWakeLock";
import type { Direction, Mode } from "./types";

export default function App() {
  const { webConnected, brokerConnected, carStatus, telemetry, camera, logs, send } = useCar();

  useWakeLock(webConnected);

  const move = useCallback((dir: Direction, label?: string) => send({ type: "move", dir }, label), [send]);
  const setMode = useCallback((mode: Mode, label: string) => send({ type: "mode", mode }, `Chuyển sang ${label}`), [send]);

  return (
    <main>
      <StatusBar web={webConnected} broker={brokerConnected} car={carStatus} />
      <CameraView camera={camera} carOnline={carStatus === "online"} telemetry={telemetry} />
      <div className="side">
        <TelemetryCard t={telemetry} />
        <ModeSwitch current={telemetry?.mode} onChange={setMode} />
        <DPad disabled={telemetry?.mode === "auto"} onMove={move} />
        <SettingsCard
          thresholdCm={telemetry?.threshold_cm}
          speed={telemetry?.speed}
          onThreshold={(cm) => send({ type: "config", threshold_cm: cm }, "Cập nhật ngưỡng")}
          onSpeed={(s) => send({ type: "config", speed: s }, "Cập nhật tốc độ")}
        />
        <EventLog logs={logs} />
      </div>
    </main>
  );
}
