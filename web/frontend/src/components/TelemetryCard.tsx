import type { Telemetry } from "../types";

export function TelemetryCard({ t }: { t: Telemetry | null }) {
  const d = t?.distance_cm ?? null;
  const near = t != null && d != null && d < t.threshold_cm;

  return (
    <section className="card telemetry">
      <div>
        <div className="label">Khoảng cách</div>
        <div className={near ? "big near" : "big"}>
          {d == null ? "--" : d.toFixed(0)} <small>cm</small>
        </div>
      </div>
      <div>
        <div className="label">Chế độ</div>
        <div>{t ? (t.mode === "auto" ? "Tự động" : "Thủ công") : "--"}</div>
        <div className="label">Trạng thái</div>
        <div>{t?.state ?? "--"}</div>
      </div>
    </section>
  );
}
