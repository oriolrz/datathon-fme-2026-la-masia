import { useEffect, useMemo, useState } from "react";
import { fmt, fmtInt, groupMetrics, hourlyContribution, monthLabel, unique, weekLabel } from "../data";
import { axis, baseOption, slider } from "../theme";
import { Chart } from "../components/Chart";
import { AgentTag, Card, PageHead, Seg, type AppCtx } from "../components/ui";

const DOW = ["dl", "dt", "dc", "dj", "dv", "ds", "dg"];

export function Operacio({ c }: { c: AppCtx }) {
  const { d, main, cmp, period, opts, k } = c;
  const weeks = useMemo(() => {
    const ws = unique(d.week.filter((_, t) => !period.mask || period.mask[t]));
    return ws;
  }, [d, period]);
  const [win, setWin] = useState<string>(c.focusWeek && weeks.includes(c.focusWeek) ? c.focusWeek : weeks[0]);
  useEffect(() => { if (c.focusWeek && weeks.includes(c.focusWeek)) setWin(c.focusWeek); }, [c.focusWeek]);
  useEffect(() => { if (win !== "all" && !weeks.includes(win)) setWin(weeks[0]); }, [weeks]);

  const idx = useMemo(() => {
    const out: number[] = [];
    for (let t = 0; t < d.t.length; t++) {
      if (period.mask && !period.mask[t]) continue;
      if (win !== "all" && d.week[t] !== win) continue;
      out.push(t);
    }
    return out;
  }, [d, period, win]);

  const [hover, setHover] = useState<number | null>(null);
  const [showCmp, setShowCmp] = useState<"si" | "no">("si");
  const contribMain = useMemo(() => hourlyContribution(d, main, opts, period.mask), [d, main, opts, period]);
  const contribCmp = useMemo(() => hourlyContribution(d, cmp, opts, period.mask), [d, cmp, opts, period]);

  const weekScores = useMemo(() => {
    const m = new Map(groupMetrics(d, main, d.week, opts, period.mask).map((g) => [g.key, g]));
    const o = new Map(groupMetrics(d, cmp, d.week, opts, period.mask).map((g) => [g.key, g]));
    return { m, o };
  }, [d, main, cmp, opts, period]);

  const option = useMemo(() => {
    const cats = idx.map((t) => d.t[t]);
    const lbl = (v: string) => `${DOW[d.dow[d.t.indexOf(v)]] ?? ""} ${v.slice(8, 10)}/${v.slice(5, 7)} ${v.slice(11, 13)}h`;
    const s = d.s;
    const both = showCmp === "si";
    const grids = [
      { left: 64, right: 64, top: 30, height: "17%" },
      { left: 64, right: 64, top: "29%", height: "19%" },
      { left: 64, right: 64, top: "54%", height: "19%" },
      { left: 64, right: 64, top: "79%", height: "13%" },
    ];
    const xa = (i: number) => axis(k, {
      type: "category", gridIndex: i, data: cats, boundaryGap: i === 2,
      axisLabel: { show: i === 3, color: k.muted, formatter: (v: string) => (v.slice(11, 13) === "00" ? `${v.slice(8, 10)}/${v.slice(5, 7)}` : ""), interval: 0, hideOverlap: true },
      splitLine: { show: true, interval: (j: number) => cats[j]?.slice(11, 13) === "00", lineStyle: { color: k.grid } },
    });
    const infrPts = idx.map((t, j) => (main.infr[t] ? j : -1)).filter((j) => j >= 0);
    return {
      ...baseOption(k),
      axisPointer: { link: [{ xAxisIndex: "all" }], label: { backgroundColor: k.ink } },
      tooltip: { ...baseOption(k).tooltip, trigger: "axis", axisPointer: { type: "line", lineStyle: { color: k.muted } },
        formatter: (ps: any[]) => {
          if (!ps.length) return "";
          const head = `<b>${lbl(ps[0].axisValue)}</b>`;
          return head + "<br/>" + ps.map((p) => `${p.marker}${p.seriesName}: <b>${typeof p.value === "number" ? fmt(p.value, p.value < 1 && p.value > -1 ? 3 : 0) : p.value}</b>`).join("<br/>");
        } },
      legend: { ...baseOption(k).legend, type: "scroll" },
      dataZoom: [{ type: "inside", xAxisIndex: [0, 1, 2, 3] }, ...(win === "all" ? [slider(k, { xAxisIndex: [0, 1, 2, 3], bottom: 0 })] : [])],
      grid: grids,
      xAxis: [0, 1, 2, 3].map(xa),
      yAxis: [
        axis(k, { gridIndex: 0, type: "value", name: "€/kWh", nameTextStyle: { color: k.price }, splitNumber: 3, axisLabel: { color: k.price, fontSize: 10 } }),
        axis(k, { gridIndex: 0, type: "value", name: "kg/kWh", position: "right", splitLine: { show: false }, splitNumber: 3, nameTextStyle: { color: k.co2 }, axisLabel: { color: k.co2, fontSize: 10 } }),
        axis(k, { gridIndex: 1, type: "value", name: "kW", splitNumber: 3 }),
        axis(k, { gridIndex: 2, type: "value", name: "kW bateria", splitNumber: 4, min: -500, max: 500 }),
        axis(k, { gridIndex: 3, type: "value", name: "SOC %", min: 0, max: 100, splitNumber: 2 }),
      ],
      series: [
        { name: "Preu PVPC", type: "line", xAxisIndex: 0, yAxisIndex: 0, showSymbol: false, step: "end", lineStyle: { width: 1.6, color: k.price }, itemStyle: { color: k.price }, data: idx.map((t) => s.price[t]) },
        { name: "CO₂ xarxa", type: "line", xAxisIndex: 0, yAxisIndex: 1, showSymbol: false, step: "end", lineStyle: { width: 1.6, color: k.co2 }, itemStyle: { color: k.co2 }, data: idx.map((t) => s.co2[t]) },
        { name: "Consum campus", type: "line", xAxisIndex: 1, yAxisIndex: 2, showSymbol: false, lineStyle: { width: 1.2, color: k.load }, itemStyle: { color: k.load }, areaStyle: { color: k.load, opacity: 0.08 }, data: idx.map((t) => +s.load[t].toFixed(0)) },
        { name: "Solar FV", type: "line", xAxisIndex: 1, yAxisIndex: 2, showSymbol: false, lineStyle: { width: 1.2, color: k.pv }, itemStyle: { color: k.pv }, areaStyle: { color: k.pv, opacity: 0.25 }, data: idx.map((t) => +s.pv[t].toFixed(0)) },
        { name: `Importació xarxa · ${main.label}`, type: "line", xAxisIndex: 1, yAxisIndex: 2, showSymbol: false, lineStyle: { width: 1.8, color: k.grid_import }, itemStyle: { color: k.grid_import }, data: idx.map((t) => +Math.max(0, s.load[t] - s.pv[t] + main.applied[t]).toFixed(0)) },
        { name: main.label, type: "bar", xAxisIndex: 2, yAxisIndex: 3, barGap: "0%", barCategoryGap: "10%", itemStyle: { color: main.color }, data: idx.map((t) => +main.applied[t].toFixed(0)),
          markPoint: infrPts.length ? { symbol: "pin", symbolSize: 26, itemStyle: { color: k.bad }, label: { formatter: "!", color: "#fff" }, data: infrPts.map((j) => ({ coord: [j, main.applied[idx[j]]] })) } : undefined },
        ...(both ? [{ name: cmp.label, type: "bar", xAxisIndex: 2, yAxisIndex: 3, itemStyle: { color: cmp.color, opacity: 0.55 }, data: idx.map((t) => +cmp.applied[t].toFixed(0)) }] : []),
        { name: `SOC · ${main.label}`, type: "line", xAxisIndex: 3, yAxisIndex: 4, showSymbol: false, lineStyle: { width: 2, color: main.color }, itemStyle: { color: main.color }, areaStyle: { color: main.color, opacity: 0.1 }, data: idx.map((t) => +(main.soc[t] / 20).toFixed(1)) },
        ...(both ? [{ name: `SOC · ${cmp.label}`, type: "line", xAxisIndex: 3, yAxisIndex: 4, showSymbol: false, lineStyle: { width: 1.4, type: "dashed", color: cmp.color }, itemStyle: { color: cmp.color }, data: idx.map((t) => +(cmp.soc[t] / 20).toFixed(1)) }] : []),
      ],
    };
  }, [idx, d, k, main, cmp, showCmp, win]);

  const t = hover !== null ? idx[hover] : idx[0];
  const detail = useMemo(() => {
    if (t === undefined) return null;
    const end = Math.min(t + 24, d.t.length);
    const win24 = Array.from({ length: end - t }, (_, i) => d.w[t + i]);
    const rank = 1 + win24.slice(1).filter((x) => x < d.w[t]).length;
    return { rank, of: win24.length, w: d.w[t] };
  }, [t, d]);

  const months = unique(weeks.map((w) => w.slice(0, 7)));
  const wm = weekScores.m.get(win), wo = weekScores.o.get(win);

  return (
    <>
      <PageHead title="Operació hora a hora"
        question={<>Pregunta: <b>quan carrega o descarrega cada política, i té sentit amb el preu i el CO₂ d'aquell moment?</b> Passa el cursor pel gràfic per veure el context de la decisió.</>}
        right={<div style={{ display: "flex", gap: 8, alignItems: "center" }}><span className="note">Mostrar comparació</span><Seg value={showCmp} onChange={setShowCmp} options={[{ v: "si", l: "Sí" }, { v: "no", l: "No" }]} /></div>} />

      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 18, flexWrap: "wrap", alignItems: "flex-start" }}>
          {months.map((m) => (
            <div key={m}>
              <div className="note" style={{ marginBottom: 4, fontWeight: 600 }}>{monthLabel(m)}</div>
              <div className="weeks">
                {weeks.filter((w) => w.startsWith(m)).map((w) => {
                  const g = weekScores.m.get(w);
                  return <button key={w} className={win === w ? "on" : ""} onClick={() => setWin(w)} title={`Score ${fmt(g?.scoreRaw ?? 0)}`}>{w.slice(8)} · {fmt(g?.scoreRaw ?? 0, 1)}</button>;
                })}
              </div>
            </div>
          ))}
          <div><div className="note" style={{ marginBottom: 4, fontWeight: 600 }}>Tot</div><div className="weeks"><button className={win === "all" ? "on" : ""} onClick={() => setWin("all")}>Període sencer</button></div></div>
        </div>
        <div className="note" style={{ marginTop: 8 }}>Cada botó mostra el score de la setmana per a <b>{main.label}</b>. S1 = dies 1–7, S2 = 8–14, S3 = 15–21, S4 = 22 en endavant.</div>
      </Card>

      <div className="grid g-op">
        <Card title={win === "all" ? "Període sencer" : `Setmana ${weekLabel(win)}`}
          sub="De dalt a baix: senyals de mercat · energia del campus · consigna aplicada (+ càrrega / − descàrrega) · estat de càrrega"
          how={<><b>Com llegir-ho:</b> una bona política carrega (barres positives) quan el preu i el CO₂ són baixos, i descarrega quan són alts, sense quedar-se buida abans del pic del vespre.</>}>
          <Chart option={option as any} height={640} onEvents={{ updateAxisPointer: (e: any) => { const v = e.axesInfo?.[0]?.value; if (typeof v === "number") setHover(v); } }} />
        </Card>
        <div className="stack">
          {win !== "all" && wm && (
            <Card title="Score de la setmana">
              <div className="kv">
                <span><AgentTag a={main} /></span><span>{fmt(wm.scoreRaw)}</span>
                <span><AgentTag a={cmp} /></span><span>{fmt(wo?.scoreRaw ?? 0)}</span>
                <span>ΔCO₂ / ΔCost</span><span>{fmt(wm.co2Pct)}% · {fmt(wm.costPct)}%</span>
                <span>Infraccions</span><span>{wm.infr}</span>
              </div>
            </Card>
          )}
          {t !== undefined && detail && (
            <Card title="Context de la decisió" sub={`${d.t[t].replace("T", " ")}:00 · ${DOW[d.dow[t]]}`}>
              <div className="kv">
                <span>Preu PVPC</span><span>{fmt(d.s.price[t], 4)} €/kWh</span>
                <span>CO₂ xarxa</span><span>{fmt(d.s.co2[t], 3)} kg/kWh</span>
                <span>Consum / solar</span><span>{fmtInt(d.s.load[t])} / {fmtInt(d.s.pv[t])} kW</span>
                <span title="0,7·CO₂/CO₂base + 0,3·preu/costbase, normalitzat a mitjana 1">Cost social del kWh</span><span>{fmt(detail.w, 2)}×</span>
                <span>Rànquing a les 24 h vistes</span><span>{detail.rank} de {detail.of}</span>
              </div>
              <div className="section-title">Decisions</div>
              <div className="kv">
                <span><AgentTag a={main} /></span><span>{fmtInt(main.applied[t])} kW</span>
                <span>SOC després</span><span>{fmt(main.soc[t] / 20, 0)}%</span>
                <span>Aportació al score</span><span>{fmt(contribMain[t], 4)}</span>
                <span><AgentTag a={cmp} /></span><span>{fmtInt(cmp.applied[t])} kW</span>
                <span>SOC després</span><span>{fmt(cmp.soc[t] / 20, 0)}%</span>
                <span>Aportació al score</span><span>{fmt(contribCmp[t], 4)}</span>
              </div>
              <p className="note" style={{ marginBottom: 0 }}>Rànquing 1 = l'hora més barata i neta de les 24 visibles (el moment ideal per carregar); {detail.of} = la més cara i bruta (el moment ideal per descarregar).</p>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
