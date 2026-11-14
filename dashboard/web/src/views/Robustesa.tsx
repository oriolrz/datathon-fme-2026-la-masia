import { useMemo, useState } from "react";
import { agentMetrics, fmt, groupMetrics, monthLabel, quantiles, unique, weekLabel, type GroupStat } from "../data";
import { axis, baseOption } from "../theme";
import { Chart } from "../components/Chart";
import { AgentTag, Card, PageHead, Seg, Swatch, type AppCtx } from "../components/ui";

const MIN_WEEK_H = 120; // les setmanes S4 del train són curtes (1–3 dies) i no entren al boxplot

export function Robustesa({ c }: { c: AppCtx }) {
  const { d, agents, main, cmp, period, opts, k } = c;
  const mask = period.mask;
  const [unit, setUnit] = useState<"week" | "day">("week");
  const keys = unit === "week" ? d.week : d.day;
  const minH = unit === "week" ? MIN_WEEK_H : 24;

  const stats = useMemo(() => agents.map((a) => {
    const g = groupMetrics(d, a, keys, opts, mask).filter((x) => x.hours >= minH);
    return { a, g, q: quantiles(g.map((x) => x.scoreRaw)) };
  }), [agents, d, keys, opts, mask, minH]);

  const boxOpt = useMemo(() => {
    const outliers: { v: [number, number]; key: string; agent: string }[] = [];
    stats.forEach((s, i) => s.g.forEach((x) => { if (x.scoreRaw < s.q.lf || x.scoreRaw > s.q.uf) outliers.push({ v: [i, x.scoreRaw], key: x.key, agent: s.a.id }); }));
    const jitter = stats.flatMap((s, i) => s.g.map((x, j) => ({ value: [i + ((j * 37) % 17 - 8) / 40, x.scoreRaw], key: x.key, itemStyle: { color: s.a.color, opacity: 0.35 } })));
    return {
      ...baseOption(k),
      grid: { left: 56, right: 20, top: 40, bottom: 60 },
      legend: { show: false },
      tooltip: { ...baseOption(k).tooltip, trigger: "item", formatter: (p: any) => {
        if (p.seriesType === "boxplot") {
          const [, lo, q1, q2, q3, hi] = p.data.value ?? p.data;
          return `<b>${stats[p.dataIndex].a.label}</b><br/>bigoti superior ${fmt(hi)}<br/>Q3 ${fmt(q3)}<br/>mediana <b>${fmt(q2)}</b><br/>Q1 ${fmt(q1)}<br/>bigoti inferior ${fmt(lo)}<br/>IQR ${fmt(q3 - q1)}`;
        }
        const key = p.data.key;
        return `<b>${unit === "week" ? weekLabel(key) : key}</b><br/>score ${fmt(p.value[1])}${p.seriesName === "outliers" ? "<br/><i>atípic (fora de les tanques de Tukey) · clica per obrir-lo</i>" : ""}`;
      } },
      xAxis: axis(k, { type: "category", data: stats.map((s) => s.a.label), axisLabel: { color: k.ink2, interval: 0, width: 110, overflow: "break", fontSize: 11 } }),
      yAxis: axis(k, { type: "value", name: `score per ${unit === "week" ? "setmana" : "dia"} (sense truncar)` }),
      series: [
        { name: "box", type: "boxplot", data: stats.map((s) => ({ value: [s.q.min, s.q.q1, s.q.q2, s.q.q3, s.q.max], itemStyle: { color: s.a.color + "22", borderColor: s.a.color, borderWidth: 1.6 } })), boxWidth: ["30%", "52%"] },
        { name: "punts", type: "scatter", symbolSize: 5, data: jitter, z: 3 },
        { name: "outliers", type: "scatter", symbol: "circle", symbolSize: 10, z: 4,
          itemStyle: { color: "transparent", borderColor: k.bad, borderWidth: 2 }, data: outliers.map((o) => ({ value: o.v, key: o.key })) },
        { type: "line", silent: true, data: [], markLine: { silent: true, symbol: "none", lineStyle: { color: k.muted, type: "dashed" }, label: { color: k.muted, position: "insideEndTop", formatter: "0 = igual que sense bateria" }, data: [{ yAxis: 0 }] } },
      ],
    };
  }, [stats, k, unit]);

  // Comparativa directa principal vs comparació
  const h2h = useMemo(() => {
    const gm = stats.find((s) => s.a.id === main.id)!.g;
    const go = new Map(stats.find((s) => s.a.id === cmp.id)!.g.map((x) => [x.key, x]));
    const pairs = gm.map((x) => ({ key: x.key, m: x.scoreRaw, o: go.get(x.key)?.scoreRaw ?? 0 }));
    const wins = pairs.filter((p) => p.m > p.o + 1e-9).length;
    const worst = [...pairs].sort((a, b) => a.m - b.m)[0];
    const best = [...pairs].sort((a, b) => b.m - a.m)[0];
    return { pairs, wins, worst, best, n: pairs.length };
  }, [stats, main, cmp]);

  const monthOpt = useMemo(() => {
    const months = unique(d.month.filter((_, t) => !mask || mask[t]));
    const show = agents.filter((a) => a.id !== "standby" && a.id !== "plantilla_oficial");
    const data = show.map((a) => new Map(groupMetrics(d, a, d.month, opts, mask).map((g) => [g.key, g])));
    return {
      ...baseOption(k),
      grid: { left: 50, right: 16, top: 60, bottom: 30 },
      legend: { ...baseOption(k).legend, type: "scroll" },
      tooltip: { ...baseOption(k).tooltip, trigger: "axis", valueFormatter: (v: number) => fmt(v) + " pts" },
      xAxis: axis(k, { type: "category", data: months.map(monthLabel) }),
      yAxis: axis(k, { type: "value", name: "score del mes" }),
      series: show.map((a, i) => ({ name: a.label, type: a.implementable ? "bar" : "line", data: months.map((m) => +(data[i].get(m)?.scoreRaw ?? 0).toFixed(3)),
        itemStyle: { color: a.color }, lineStyle: { type: "dashed", color: a.color }, symbol: "diamond", symbolSize: 8, barMaxWidth: 18 })),
    };
  }, [agents, d, opts, mask, k]);

  // Partició A/B per mesos alterns: si una política «guanya» només en una meitat, probablement està sobreajustada
  const split = useMemo(() => {
    const months = unique(d.month);
    const A = new Set(months.filter((_, i) => i % 2 === 0));
    const mA = Uint8Array.from(d.month, (m, t) => (A.has(m) && (!mask || mask[t]) ? 1 : 0));
    const mB = Uint8Array.from(d.month, (m, t) => (!A.has(m) && (!mask || mask[t]) ? 1 : 0));
    return { A: [...A], rows: agents.map((a) => ({ a, sa: agentMetrics(d, a, opts, mA).score, sb: agentMetrics(d, a, opts, mB).score })) };
  }, [agents, d, opts, mask]);

  const open = (key: string) => { if (unit === "week") c.goTo("operacio", key); };

  return (
    <>
      <PageHead title="Robustesa · anàlisi de Tukey"
        question={<>Pregunta: <b>la política funciona bé cada setmana o només de mitjana?</b> Al test ocult hi ha 12 setmanes; una política amb molta variància és arriscada.</>}
        right={<Seg value={unit} onChange={setUnit} options={[{ v: "week", l: "Per setmana" }, { v: "day", l: "Per dia" }]} />} />
      <div className="grid g-21" style={{ marginBottom: 16 }}>
        <Card title={`Distribució del score per ${unit === "week" ? "setmana" : "dia"}`}
          sub={<>Diagrama de caixa de Tukey: la caixa va de Q1 a Q3, la línia és la mediana, els bigotis arriben fins a 1,5·IQR i els cercles vermells són valors atípics. {unit === "week" ? `Només setmanes de ≥ ${MIN_WEEK_H} h.` : ""}</>}
          how={<><b>Decisió:</b> per al test, una caixa alta i estreta (bona mediana, poca dispersió) val més que una mitjana alta amb una cua de setmanes negatives. {unit === "week" && "Clica un atípic per obrir la setmana a «Operació»."}</>}>
          <Chart option={boxOpt as any} height={400} onEvents={{ click: (p) => { if (p.data?.key) open(p.data.key); } }} />
        </Card>
        <Card title="Duel directe" sub={<><AgentTag a={main} /> vs <AgentTag a={cmp} /></>}>
          <div className="big-number">{h2h.wins}<span style={{ fontSize: 18, color: "var(--muted)" }}> / {h2h.n}</span></div>
          <div className="note" style={{ marginBottom: 12 }}>{unit === "week" ? "setmanes" : "dies"} en què {main.label} supera {cmp.label}</div>
          <div className="kv">
            <span>Mediana (Q2)</span><span>{fmt(stats.find((s) => s.a.id === main.id)!.q.q2)}</span>
            <span>IQR (dispersió)</span><span>{fmt(stats.find((s) => s.a.id === main.id)!.q.iqr)}</span>
            {h2h.worst && <><span>Pitjor {unit === "week" ? "setmana" : "dia"}</span><span><a href="#" onClick={(e) => { e.preventDefault(); open(h2h.worst.key); }}>{unit === "week" ? weekLabel(h2h.worst.key) : h2h.worst.key}</a> · {fmt(h2h.worst.m)}</span></>}
            {h2h.best && <><span>Millor {unit === "week" ? "setmana" : "dia"}</span><span><a href="#" onClick={(e) => { e.preventDefault(); open(h2h.best.key); }}>{unit === "week" ? weekLabel(h2h.best.key) : h2h.best.key}</a> · {fmt(h2h.best.m)}</span></>}
          </div>
          <div className="section-title">Validació A/B per mesos alterns</div>
          <table className="t">
            <thead><tr><th>Agent</th><th className="num">Meitat A</th><th className="num">Meitat B</th><th className="num">Δ</th></tr></thead>
            <tbody>
              {split.rows.filter((r) => r.a.id !== "standby").map((r) => (
                <tr key={r.a.id} className={r.a.id === main.id ? "sel" : ""}>
                  <td><Swatch color={r.a.color} />{r.a.label}</td>
                  <td className="num">{fmt(r.sa)}</td><td className="num">{fmt(r.sb)}</td>
                  <td className="num" style={{ color: Math.abs(r.sa - r.sb) > 1 ? "var(--warn)" : undefined }}>{fmt(r.sa - r.sb)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="note">A = {split.A.map(monthLabel).join(", ")}. Si ajusteu paràmetres al laboratori, mireu que la millora es mantingui a totes dues meitats.</p>
        </Card>
      </div>
      <div className="grid g-12">
        <WeekTable c={c} stats={stats} unit={unit} onOpen={open} />
        <Card title="Score per mes" sub="Barres: polítiques implementables · línia discontínua: òptim teòric"
          how={<><b>Decisió:</b> en els mesos en què la distància amb l'òptim és més gran hi ha més marge per a una política estacional (paràmetres diferents segons el mes).</>}>
          <Chart option={monthOpt as any} height={360} />
        </Card>
      </div>
    </>
  );
}

function WeekTable({ c, stats, unit, onOpen }: { c: AppCtx; stats: { a: any; g: GroupStat[] }[]; unit: string; onOpen: (k: string) => void }) {
  const show = stats.filter((s) => s.a.id !== "standby" && s.a.id !== "plantilla_oficial");
  const keys = show[0]?.g.map((x) => x.key) ?? [];
  const maps = show.map((s) => new Map(s.g.map((x) => [x.key, x.scoreRaw])));
  const all = maps.flatMap((m) => [...m.values()]);
  const max = Math.max(...all, 1), min = Math.min(...all, -1);
  const color = (v: number) => v >= 0 ? `color-mix(in srgb, var(--accent) ${Math.round((v / max) * 55)}%, transparent)` : `color-mix(in srgb, var(--bad) ${Math.round((v / min) * 55)}%, transparent)`;
  if (unit !== "week") return <Card title="Taula setmanal"><p className="note">Canvia a «Per setmana» per veure la taula.</p></Card>;
  return (
    <Card title="Taula setmanal" sub="Score de cada setmana. Clica una fila per obrir-la.">
      <div style={{ maxHeight: 360, overflow: "auto" }}>
        <table className="t">
          <thead><tr><th>Setmana</th>{show.map((s) => <th key={s.a.id} className="num" title={s.a.label}><Swatch color={s.a.color} /></th>)}</tr></thead>
          <tbody>
            {keys.map((key) => (
              <tr key={key} className="click" onClick={() => onOpen(key)}>
                <td>{weekLabel(key)}</td>
                {maps.map((m, i) => { const v = m.get(key) ?? 0; return <td key={i} className="num" style={{ background: color(v) }}>{fmt(v, 1)}</td>; })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
