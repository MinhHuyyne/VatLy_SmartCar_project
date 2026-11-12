import { useEffect, useRef, useState, type PointerEvent } from "react";
import { buzz } from "../haptics";
import { DIR_LABEL, type Direction } from "../types";

interface Props {
  disabled: boolean;
  onMove: (dir: Direction, label?: string) => void;
}

// Bố cục 3x3, null = ô trống
const LAYOUT: (Direction | null)[] = [null, "forward", null, "left", "stop", "right", null, "backward", null];
const ICON: Record<Direction, string> = { forward: "▲", backward: "▼", left: "◀", right: "▶", stop: "■" };
const KEYS: Record<string, Direction> = { w: "forward", s: "backward", a: "left", d: "right", " ": "stop" };

/** Giữ nút để chạy, thả ra xe dừng. Trên máy tính dùng W A S D, Space = dừng. */
export function DPad({ disabled, onMove }: Props) {
  const [pressed, setPressed] = useState<Direction | null>(null);
  const pressedRef = useRef<Direction | null>(null); // tránh gửi "stop" 2 lần (pointerup + pointerleave)

  const start = (dir: Direction) => (e: PointerEvent) => {
    e.preventDefault();
    (e.currentTarget as Element).setPointerCapture?.(e.pointerId); // trượt ngón tay ra ngoài vẫn giữ nút
    buzz(dir === "stop" ? 30 : 12);
    pressedRef.current = dir;
    setPressed(dir);
    onMove(dir, DIR_LABEL[dir]);
  };

  const end = (dir: Direction) => (e: PointerEvent) => {
    e.preventDefault();
    if (pressedRef.current !== dir) return;
    pressedRef.current = null;
    setPressed(null);
    if (dir !== "stop") onMove("stop", DIR_LABEL.stop);
  };

  useEffect(() => {
    if (disabled) return;
    const down = (e: KeyboardEvent) => {
      const dir = KEYS[e.key];
      if (e.repeat || !dir) return;
      onMove(dir, DIR_LABEL[dir]);
    };
    const up = (e: KeyboardEvent) => {
      const dir = KEYS[e.key];
      if (dir && dir !== "stop") onMove("stop");
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [disabled, onMove]);

  return (
    <>
      <section className={disabled ? "card pad disabled" : "card pad"}>
        {LAYOUT.map((dir, i) =>
          dir == null ? (
            <span key={i} />
          ) : (
            <button
              key={dir}
              aria-label={DIR_LABEL[dir]}
              className={["dir", dir === "stop" && "stop", pressed === dir && "pressed"].filter(Boolean).join(" ")}
              onPointerDown={start(dir)}
              onPointerUp={end(dir)}
              onPointerLeave={end(dir)}
              onPointerCancel={end(dir)}
              onContextMenu={(e) => e.preventDefault()}
            >
              {ICON[dir]}
            </button>
          ),
        )}
      </section>
      <p className="hint">{disabled ? "Đang ở chế độ tự động." : "Giữ nút để chạy, thả ra xe dừng."}</p>
    </>
  );
}
