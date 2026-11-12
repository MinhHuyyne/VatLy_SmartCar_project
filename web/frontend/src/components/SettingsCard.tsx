import { useEffect, useState } from "react";

interface SliderProps {
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  value: number | undefined;
  onCommit: (v: number) => void;
}

function Slider({ label, unit, min, max, step, value, onCommit }: SliderProps) {
  const [draft, setDraft] = useState(value ?? min);

  // Đồng bộ lại khi xe báo giá trị mới
  useEffect(() => {
    if (value != null) setDraft(value);
  }, [value]);

  return (
    <label>
      {label}: <b>{draft}</b>
      {unit}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={draft}
        onChange={(e) => setDraft(Number(e.target.value))}
        onPointerUp={() => onCommit(draft)}
        onKeyUp={() => onCommit(draft)}
      />
    </label>
  );
}

interface Props {
  thresholdCm: number | undefined;
  speed: number | undefined; // 0.1..1.0 (= 10..100%)
  onThreshold: (cm: number) => void;
  onSpeed: (speed: number) => void;
}

export function SettingsCard({ thresholdCm, speed, onThreshold, onSpeed }: Props) {
  return (
    <section className="card settings">
      <Slider label="Ngưỡng vật cản" unit=" cm" min={5} max={100} step={1} value={thresholdCm} onCommit={onThreshold} />
      <Slider
        label="Tốc độ"
        unit="%"
        min={10}
        max={100}
        step={5}
        value={speed == null ? undefined : Math.round(speed * 100)}
        onCommit={(v) => onSpeed(v / 100)}
      />
    </section>
  );
}
