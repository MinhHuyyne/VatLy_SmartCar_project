import type { Mode } from "../types";

const MODES: { mode: Mode; label: string }[] = [
  { mode: "manual", label: "Thủ công" },
  { mode: "auto", label: "Tự động" },
];

interface Props {
  current: Mode | undefined;
  onChange: (mode: Mode, label: string) => void;
}

export function ModeSwitch({ current, onChange }: Props) {
  return (
    <section className="card mode-card">
      <div className="mode-switch">
        {MODES.map(({ mode, label }) => (
          <button
            key={mode}
            className={current === mode ? "mode-btn active" : "mode-btn"}
            onClick={() => onChange(mode, label)}
          >
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}
