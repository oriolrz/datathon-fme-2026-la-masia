import { useEffect, useRef } from "react";
import * as echarts from "echarts";

type Handler = (p: any) => void;

export function Chart({ option, height = 320, onEvents, group }: {
  option: echarts.EChartsOption; height?: number; onEvents?: Record<string, Handler>; group?: string;
}) {
  const el = useRef<HTMLDivElement>(null);
  const inst = useRef<echarts.ECharts | null>(null);
  const handlers = useRef(onEvents);
  handlers.current = onEvents;

  useEffect(() => {
    if (!el.current) return;
    const c = echarts.init(el.current, undefined, { renderer: "canvas" });
    inst.current = c;
    const ro = new ResizeObserver(() => c.resize());
    ro.observe(el.current);
    return () => { ro.disconnect(); c.dispose(); inst.current = null; };
  }, []);

  useEffect(() => {
    const c = inst.current;
    if (!c) return;
    c.setOption(option, { notMerge: true, lazyUpdate: true });
    if (group) { c.group = group; echarts.connect(group); }
  }, [option, group]);

  useEffect(() => {
    const c = inst.current;
    if (!c) return;
    const names = Object.keys(onEvents ?? {});
    names.forEach((n) => c.on(n, (p: any) => handlers.current?.[n]?.(p)));
    return () => names.forEach((n) => c.off(n));
  }, [onEvents ? Object.keys(onEvents).join() : ""]);

  return <div ref={el} style={{ width: "100%", height }} />;
}
