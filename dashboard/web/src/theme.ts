// Tokens per als gràfics (ECharts no llegeix variables CSS directament).
export interface Tokens {
  dark: boolean; ink: string; ink2: string; muted: string; grid: string; border: string; surface: string;
  accent: string; price: string; co2: string; load: string; pv: string; grid_import: string; good: string; bad: string;
  diverging: string[];
}

export function tokens(dark: boolean): Tokens {
  return dark
    ? {
        dark, ink: "#e7ebf1", ink2: "#c3cad6", muted: "#8b95a7", grid: "#1d293a", border: "#2f3f56", surface: "#121a26",
        accent: "#34c39b", price: "#e0a84a", co2: "#a78bfa", load: "#8fb3ff", pv: "#f6c343", grid_import: "#f07167",
        good: "#4ade80", bad: "#f07167",
        diverging: ["#ef6f5e", "#f3a68f", "#2a3445", "#7cc7b0", "#2fae8c"],
      }
    : {
        dark, ink: "#0e1726", ink2: "#3b4658", muted: "#6b7587", grid: "#eef1f5", border: "#d9dee6", surface: "#ffffff",
        accent: "#0f8a6a", price: "#c27c0e", co2: "#7c3aed", load: "#2f6fed", pv: "#e8a400", grid_import: "#c2413a",
        good: "#15803d", bad: "#c2413a",
        diverging: ["#c2413a", "#ef9f8f", "#f3f4f6", "#86cdb6", "#0f8a6a"],
      };
}

export function baseOption(k: Tokens) {
  return {
    backgroundColor: "transparent",
    textStyle: { fontFamily: "Inter Variable, Inter, system-ui, sans-serif", color: k.ink2, fontSize: 12 },
    animationDuration: 350,
    tooltip: {
      backgroundColor: k.surface, borderColor: k.border, textStyle: { color: k.ink, fontSize: 12 },
      extraCssText: "box-shadow:0 6px 20px rgba(0,0,0,.12);border-radius:8px;",
    },
    legend: { textStyle: { color: k.ink2 }, icon: "roundRect", itemWidth: 12, itemHeight: 8, top: 0 },
  };
}

export function slider(k: Tokens, extra: Record<string, unknown> = {}) {
  return {
    type: "slider", height: 16, bottom: 8, borderColor: k.border, backgroundColor: "transparent",
    fillerColor: k.dark ? "rgba(52,195,155,0.18)" : "rgba(15,138,106,0.12)",
    dataBackground: { lineStyle: { color: k.border }, areaStyle: { color: k.grid } },
    selectedDataBackground: { lineStyle: { color: k.accent }, areaStyle: { color: k.accent, opacity: 0.15 } },
    handleStyle: { color: k.surface, borderColor: k.muted }, moveHandleStyle: { color: k.border },
    textStyle: { color: k.muted, fontSize: 10 }, ...extra,
  };
}

export function axis(k: Tokens, extra: Record<string, unknown> = {}) {
  return {
    axisLine: { lineStyle: { color: k.border } },
    axisTick: { show: false },
    axisLabel: { color: k.muted, fontSize: 11 },
    splitLine: { lineStyle: { color: k.grid } },
    nameTextStyle: { color: k.muted, fontSize: 11 },
    ...extra,
  };
}
