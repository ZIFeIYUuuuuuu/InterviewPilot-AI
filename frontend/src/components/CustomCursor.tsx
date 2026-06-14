import { useEffect, useRef, useState } from "react";

const interactiveSelector = [
  "button:not(:disabled)",
  "a[href]",
  "select",
  "input",
  "textarea",
  "[role='button']",
  ".question-template-card",
  ".resume-dropzone",
].join(",");

export function CustomCursor() {
  const pointerRef = useRef<HTMLSpanElement | null>(null);
  const ringRef = useRef<HTMLSpanElement | null>(null);
  const target = useRef({ x: 0, y: 0 });
  const ring = useRef({ x: 0, y: 0 });
  const animationFrame = useRef<number | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [active, setActive] = useState(false);
  const [magnetic, setMagnetic] = useState(false);

  useEffect(() => {
    const canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!canHover || reducedMotion) {
      return undefined;
    }

    setEnabled(true);

    function move(event: MouseEvent) {
      target.current = { x: event.clientX, y: event.clientY };
      pointerRef.current?.style.setProperty("--cursor-x", `${event.clientX}px`);
      pointerRef.current?.style.setProperty("--cursor-y", `${event.clientY}px`);
    }

    function over(event: MouseEvent) {
      const element = event.target instanceof Element ? event.target.closest(interactiveSelector) : null;
      setMagnetic(Boolean(element));
    }

    function down() {
      setActive(true);
    }

    function up() {
      setActive(false);
    }

    function tick() {
      ring.current.x += (target.current.x - ring.current.x) * 0.18;
      ring.current.y += (target.current.y - ring.current.y) * 0.18;
      ringRef.current?.style.setProperty("--cursor-x", `${ring.current.x}px`);
      ringRef.current?.style.setProperty("--cursor-y", `${ring.current.y}px`);
      animationFrame.current = window.requestAnimationFrame(tick);
    }

    window.addEventListener("mousemove", move, { passive: true });
    window.addEventListener("mouseover", over, { passive: true });
    window.addEventListener("mousedown", down, { passive: true });
    window.addEventListener("mouseup", up, { passive: true });
    animationFrame.current = window.requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseover", over);
      window.removeEventListener("mousedown", down);
      window.removeEventListener("mouseup", up);
      if (animationFrame.current !== null) {
        window.cancelAnimationFrame(animationFrame.current);
      }
    };
  }, []);

  if (!enabled) {
    return null;
  }

  return (
    <div className={`smart-cursor ${magnetic ? "is-magnetic" : ""} ${active ? "is-active" : ""}`} aria-hidden="true">
      <span className="smart-cursor__ring" ref={ringRef} />
      <span className="smart-cursor__dot" ref={pointerRef} />
    </div>
  );
}
