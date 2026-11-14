import { useMemo } from "react";
import { fmt, monthLabel, unique, type Agent } from "../data";
import { axis, baseOption } from "../theme";
import { Chart } from "../components/Chart";
import { AgentTag, Card, PageHead, type AppCtx } from "../components/ui";

export function Patrons({ c }: { c: AppCtx }) {
  const { d, main, cmp, period, k } = c;
  const mask = period.mask;
  const months = useMemo(() => unique(d.month.filter((_, t) => !mask || mask[t])), [d, mask]);

  const heat = (a: Agent) => {
    const sum = new Map<string, { s: number; n: number }>();
    for (let t = 0; t < d.t.length; t++) {
      if (mask && !mask[t]) continue;
      const key = `${d.month[t]}|${d.hour[t]}`;
      const r = sum.get(key) ?? { s: 0, n: 0 };
      r.s += a.applied[t]; r.n++; sum.set(key, r);
    }
    const data: [number, number, number][] = [];
    months.forEach((m, i) => { for (let h = 0; h < 24; h++) { const r = sum.get(`${m}|${h}`); if (r) data.push([h, i, +(r.s / r.n).toFixed(0)]); } });
    return data;
  };

  const heatOpt = (a: Agent) => ({
    ...baseOption(k),
    grid: { left: 60, right: 16, top: 10, bottom: 70 },
    tooltip: { ...baseOption(k).tooltip, formatter: (p: any) => `${monthLabel(months[p.value[1]])} · ${p.value[0]}h<br/>Potència mitjana: <b>${fmt(p.value[2], 0)} kW</b>` },
    xAxis: axis(k, { type: "category", data: Array.from({ length: 24 }, (_, h) => `${h}h`), splitArea: { show: false } }),
    yAxis: axis(k, { type: "category", data: months.map(monthLabel) }),
    visualMap: { min: -500, max: 500, calculable: true, orient: "horizontal", left: "center", bottom: 0, itemHeight: 220, itemWidth: 10,
      text: ["càrrega", "descàrrega"], textStyle: { color: k.muted, fontSize: 11 }, inRange: { color: k.diverging } },
    series: [{ type: "heatmap", data: heat(a), itemStyle: { borderColor: k.surface, borderWidth: 1 }, emphasis: { itemStyle: { borderColor: k.ink } } }],
  });

  const profileOpt = useMemo(() => {
    const acc = Array.from({ length: 24 }, () => ({ m: 0, c: 0, p: 0, e: 0, n: 0, l: 0, pv: 0 }));
    for (let t = 0; t < d.t.length; t++) {
      if (mask && !mask[t]) continue;
      const r = acc[d.hour[t]];
      r.m += main.applied[t]; r.c += cmp.applied[t]; r.p += d.s.price[t]; r.e += d.s.co2[t]; r.l += d.s.load[t]; r.pv += d.s.pv[t]; r.n++;
    }
    const hs = Array.from({ length: 24 }, (_, h) => `${h}h`);
    return {
      ...baseOption(k),
      grid: { left: 56, right: 60, top: 64, bottom: 30 },
      tooltip: { ...baseOption(k).tooltip, trigger: "axis" },
      xAxis: axis(k, { type: "category", data: hs }),
      yAxis: [axis(k, { type: "value", name: "kW mitjans", min: -500, max: 500 }),
        axis(k, { type: "value", name: "índex (mitjana = 1)", position: "right", splitLine: { show: false }, scale: true })],
      series: [
        { name: main.label, type: "bar", data: acc.map((r) => +(r.m / r.n).toFixed(0)), itemStyle: { color: main.color } },
        { name: cmp.label, type: "bar", data: acc.map((r) => +(r.c / r.n).toFixed(0)), itemStyle: { color: cmp.color, opacity: 0.55 } },
        { name: "Preu (índex)", type: "line", yAxisIndex: 1, smooth: true, showSymbol: false, lineStyle: { color: k.price, width: 2 }, itemStyle: { color: k.price },
          data: (() => { const mean = acc.reduce((s, r) => s + r.p / r.n, 0) / 24; return acc.map((r) => +((r.p / r.n) / mean).toFixed(3)); })() },
        { name: "CO₂ (índex)", type: "line", yAxisIndex: 1, smooth: true, showSymbol: false, lineStyle: { color: k.co2, width: 2 }, itemStyle: { color: k.co2 },
          data: (() => { const mean = acc.reduce((s, r) => s + r.e / r.n, 0) / 24; return acc.map((r) => +((r.e / r.n) / mean).toFixed(3)); })() },
      ],
    };
  }, [d, main, cmp, mask, k]);

  // Qualitat de l'arbitratge: energia neta per rang dins del dia del «cost social» w
  const rankOpt = useMemo(() => {
    const byDay = new Map<string, number[]>();
    for (let t = 0; t < d.t.length; t++) {
      if (mask && !mask[t]) continue;
      const arr = byDay.get(d.day[t]) ?? [];
      arr.push(t); byDay.set(d.day[t], arr);
    }
    const agents = [main, cmp];
    const acc = agents.map(() => Array.from({ length: 24 }, () => ({ ch: 0, dis: 0 })));
    let days = 0;
    for (const ts of byDay.values()) {
      if (ts.length < 24) continue;
      days++;
      const order = [...ts].sort((a, b) => d.w[a] - d.w[b]);
      order.forEach((t, r) => agents.forEach((a, i) => {
        const p = a.applied[t];
        if (p > 0) acc[i][r].ch += p; else acc[i][r].dis += p;
      }));
    }
    const cats = Array.from({ length: 24 }, (_, r) => `${r + 1}`);
    return {
      ...baseOption(k),
      grid: { left: 64, right: 16, top: 64, bottom: 44 },
      tooltip: { ...baseOption(k).tooltip, trigger: "axis", valueFormatter: (v: number) => fmt(v, 0) + " kWh/dia" },
      xAxis: axis(k, { type: "category", data: cats, name: "rang de l'hora dins el dia (1 = la més barata i neta)", nameLocation: "middle", nameGap: 28 }),
      yAxis: axis(k, { type: "value", name: "kWh/dia" }),
      series: agents.flatMap((a, i) => [
        { name: `${a.label} · càrrega`, type: "bar", stack: `a${i}`, data: acc[i].map((r) => +(r.ch / days).toFixed(1)), itemStyle: { color: a.color, opacity: i ? 0.5 : 1 } },
        { name: `${a.label} · descàrrega`, type: "bar", stack: `a${i}`, data: acc[i].map((r) => +(r.dis / days).toFixed(1)), itemStyle: { color: a.color, opacity: i ? 0.35 : 0.75, decal: { symbol: "rect", dashArrayX: [1, 0], dashArrayY: [2, 3], rotation: -0.8, color: "rgba(255,255,255,.35)" } } },
      ]),
    };
  }, [d, main, cmp, mask, k]);

  return (
    <>
      <PageHead title="Patrons de comportament"
        question={<>Pregunta: <b>la política carrega i descarrega a les hores correctes de cada dia i estació?</b> Compara <AgentTag a={main} /> amb <AgentTag a={cmp} />.</>} />
      <div className="grid g-2" style={{ marginBottom: 16 }}>
        <Card title={<>Mapa de calor hora × mes · <AgentTag a={main} /></>} sub="Potència mitjana aplicada (verd = càrrega, vermell = descàrrega)">
          <Chart option={heatOpt(main) as any} height={360} />
        </Card>
        <Card title={<>Mapa de calor hora × mes · <AgentTag a={cmp} /></>} sub="Mateixa escala: les diferències de color mostren on divergeixen les dues estratègies">
          <Chart option={heatOpt(cmp) as any} height={360} />
        </Card>
      </div>
      <div className="grid g-2">
        <Card title="Perfil diari mitjà" sub="Barres: potència mitjana per hora · línies: preu i CO₂ relatius a la mitjana diària"
          how={<><b>Decisió:</b> el CO₂ i el preu no tenen el mateix perfil. Si la política només segueix el preu, deixa de carregar a les hores solars, que són les més netes.</>}>
          <Chart option={profileOpt as any} height={330} />
        </Card>
        <Card title="Qualitat de l'arbitratge" sub="Cada dia s'ordenen les 24 hores pel seu cost social (0,7·CO₂ + 0,3·preu, amb els pesos del score). On carreguen i descarreguen les polítiques?"
          how={<><b>Ideal:</b> tota la càrrega a l'esquerra (rangs 1–6) i tota la descàrrega a la dreta (rangs 19–24). Si hi ha energia al mig, és un cicle que paga el 10% de pèrdues sense guanyar gaire.</>}>
          <Chart option={rankOpt as any} height={330} />
        </Card>
      </div>
    </>
  );
}
