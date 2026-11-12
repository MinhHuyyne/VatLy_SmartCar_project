import type { LogEntry } from "../types";

export function EventLog({ logs }: { logs: LogEntry[] }) {
  return (
    <section className="card log-card">
      <div className="label">Nhật ký</div>
      <ul className="log">
        {logs.map((l) => (
          <li key={l.id} className={l.level}>
            {l.time} {l.msg}
          </li>
        ))}
      </ul>
    </section>
  );
}
