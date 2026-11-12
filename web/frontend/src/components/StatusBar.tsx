import type { CarStatus } from "../types";

interface Props {
  web: boolean;
  broker: boolean | null;
  car: CarStatus;
}

function Pill({ label, title, on }: { label: string; title: string; on: boolean | null }) {
  const cls = on === true ? "pill on" : on === false ? "pill off" : "pill";
  return (
    <span className={cls} title={title}>
      {label}
    </span>
  );
}

export function StatusBar({ web, broker, car }: Props) {
  return (
    <header>
      <h1>Smart Car</h1>
      <div className="links">
        <Pill label="Web" title="Website ↔ Backend" on={web} />
        <Pill label="MQTT" title="Backend ↔ MQTT broker" on={broker} />
        <Pill label="Xe" title="Xe online/offline" on={car === "unknown" ? null : car === "online"} />
      </div>
    </header>
  );
}
