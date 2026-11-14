import { useMemo } from "react";
import { agentMetrics, cumulativeScore, fmt, fmtInt, groupMetrics, monthLabel, type Agent } from "../data";
import { axis, baseOption, slider } from "../theme";
import { Chart } from "../components/Chart";
import { AgentTag, Card, Delta, Icon, Kpi, PageHead, type AppCtx } from "../components/ui";

export function Resum({ c }: { c: AppCtx }) {
  const { d, agents, main, cmp, period, opts, k } = c;
  const mask = period.mask;

  const rows = useMemo(() => agents.map((a) => ({ a, m: agentMetrics(d, a, opts, mask) })), [agents, opts, mask, d]);
  const byId = (id: string) => rows.find((r) => r.a.id === id);
  const mm = byId(main.id)!.m;
  const cm = byId(cmp.id)!.m;
  const oracle = byId("oracle");
  const best = rows.filter((r) => r.a.implementable).sort((x, y) => y.m.score - x.m.score)[0];
  const ceiling = oracle?.m.score ?? NaN;

  // Mes amb menor captura del sostre per al principal
  const weakMonth = useMemo(() => {
    const o = agents.find((a) => a.id === "oracle");
    if (!o) return null;
    const gm = groupMetrics(d, main, d.month, opts, mask);
    const go = new Map(groupMetrics(d, o, d.month, opts, mask).map((g) => [g.key, g]));
    const gaps = gm.filter((g) => g.hours >= 120).map((g) => ({ key: g.key, gap: (go.get(g.key)?.scoreRaw ?? 0) - g.scoreRaw }));
    return gaps.sort((a, b) => b.gap - a.gap)[0] ?? null;
  }, [d, main, opts, mask, agents]);

  const ranking = [...rows].sort((a, b) => a.m.scoreRaw - b.m.scoreRaw);
  const rankOpt = useMemo(() => ({
    ...baseOption(k),
    grid: { left: 10, right: 40, top: 28, bottom: 10, containLabel: true },
    legend: { ...baseOption(k).legend, data: ["0,7 × ΔCO₂", "0,3 × ΔCost", "Penalització"] },
    tooltip: { ...baseOption(k).tooltip, trigger: "axis", axisPointer: { type: "shadow" },
      valueFormatter: (v: number) => fmt(v) + " pts" },
    xAxis: axis(k, { type: "value", name: "punts" }),
    yAxis: axis(k, { type: "category", data: ranking.map((r) => r.a.label), axisLabel: { color: k.ink2, fontSize: 12, width: 170, overflow: "truncate",
      formatter: (v: string) => (v === main.label ? `{b|${v}}` : v), rich: { b: { fontWeight: 700, color: k.ink } } } }),
    series: [
      { name: "0,7 × ΔCO₂", type: "bar", stack: "s", data: ranking.map((r) => ({ value: +(0.7 * r.m.co2Pct).toFixed(3), itemStyle: { color: k.co2, opacity: r.a.id === main.id ? 1 : 0.55 } })), barWidth: 16 },
      { name: "0,3 × ΔCost", type: "bar", stack: "s", data: ranking.map((r) => ({ value: +(0.3 * r.m.costPct).toFixed(3), itemStyle: { color: k.price, opacity: r.a.id === main.id ? 1 : 0.55 } })) },
      { name: "Penalització", type: "bar", stack: "s", data: ranking.map((r) => -opts.penaltyPts * r.m.infr), itemStyle: { color: k.bad },
        label: { show: true, position: "right", color: k.ink, fontWeight: 700, formatter: (p: any) => fmt(ranking[p.dataIndex].m.score) } },
    ],
  }), [ranking, k, main.label, opts.penaltyPts]);

  const scatterOpt = useMemo(() => {
    const xs = rows.map((r) => r.m.co2Pct), ys = rows.map((r) => r.m.costPct);
    const xmax = Math.max(1, ...xs) * 1.15, ymax = Math.max(1, ...ys) * 1.15;
    const xmin = Math.min(0, ...xs) - 0.3, ymin = Math.min(0, ...ys) - 0.3;
    const iso = [1, 2, 3, 4, 5, 6, 7, 8].map((S) => ({
      type: "line", silent: true, symbol: "none", lineStyle: { color: k.border, type: "dashed", width: 1 },
      data: [[xmin, (S - 0.7 * xmin) / 0.3], [(S - 0.3 * ymin) / 0.7, ymin]],
      endLabel: { show: false }, z: 1,
      markPoint: undefined,
    }));
    const yl = ymax * 0.93;
    const isoLabels = [1, 2, 3, 4, 5, 6, 7, 8].map((S) => ({ coord: [(S - 0.3 * yl) / 0.7, yl], S }))
      .filter((l) => l.coord[0] > xmin + 0.2 && l.coord[0] < xmax - 0.2);
    return {
      ...baseOption(k),
      legend: { show: false },
      grid: { left: 50, right: 20, top: 20, bottom: 45 },
      tooltip: { ...baseOption(k).tooltip, trigger: "item",
        formatter: (p: any) => p.seriesName === "agents" ? `<b>${p.data.name}</b><br/>ΔCO₂ ${fmt(p.data.value[0])}% · ΔCost ${fmt(p.data.value[1])}%<br/>Score ${fmt(p.data.score)}` : "" },
      xAxis: axis(k, { type: "value", name: "Reducció CO₂ (%)", nameLocation: "middle", nameGap: 28, min: +xmin.toFixed(1), max: +xmax.toFixed(1) }),
      yAxis: axis(k, { type: "value", name: "Estalvi cost (%)", nameLocation: "middle", nameGap: 34, min: +ymin.toFixed(1), max: +ymax.toFixed(1) }),
      series: [
        ...iso,
        { type: "scatter", silent: true, symbolSize: 0, data: isoLabels.map((l) => l.coord),
          label: { show: true, formatter: (p: any) => `score ${isoLabels[p.dataIndex].S}`, color: k.muted, fontSize: 10 } },
        { name: "agents", type: "scatter", z: 5,
          data: rows.map((r) => ({ name: r.a.label, id: r.a.id, score: r.m.score, value: [r.m.co2Pct, r.m.costPct],
            symbolSize: r.a.id === main.id ? 18 : r.a.id === cmp.id ? 15 : 11,
            symbol: r.a.implementable ? "circle" : "diamond",
            itemStyle: { color: r.a.color, borderColor: k.surface, borderWidth: 2 } })),
          label: { show: true, position: "right", color: k.ink2, fontSize: 11, formatter: (p: any) => p.data.name } },
      ],
    };
  }, [rows, k, main.id, cmp.id]);

  const cumOpt = useMemo(() => {
    const idx: number[] = [];
    for (let t = 0; t < d.t.length; t++) if (!mask || mask[t]) idx.push(t);
    // la plantilla sense clamp s'omet: les seves 46 infraccions aplanarien l'escala
    const show = agents.filter((a) => a.id !== "standby" && a.id !== "plantilla_oficial");
    return {
      ...baseOption(k),
      grid: { left: 50, right: 20, top: 30, bottom: 50 },
      tooltip: { ...baseOption(k).tooltip, trigger: "axis", valueFormatter: (v: number) => fmt(v) + " pts" },
      legend: { ...baseOption(k).legend, type: "scroll" },
      dataZoom: [{ type: "inside" }, slider(k)],
      xAxis: axis(k, { type: "category", data: idx.map((t) => d.t[t].replace("T", " ") + "h"), axisLabel: { color: k.muted, formatter: (v: string) => v.slice(5, 10) }, splitLine: { show: false } }),
      yAxis: axis(k, { type: "value", name: "punts acumulats" }),
      series: show.map((a) => ({
        name: a.label, type: "line", showSymbol: false, sampling: "lttb",
        lineStyle: { width: a.id === main.id ? 2.6 : a.id === cmp.id ? 2 : 1.2, type: a.implementable ? "solid" : "dashed", color: a.color },
        itemStyle: { color: a.color }, data: cumulativeScore(d, a, opts, mask).map((v) => +v.toFixed(3)),
      })),
    };
  }, [agents, d, opts, mask, k, main.id, cmp.id]);

  const lb = d.leaderboard;
  const v1 = byId("oriol_v1");
  const pctCeil = (s: number) => (isFinite(ceiling) && ceiling > 0 ? (100 * s) / ceiling : NaN);

  return (
    <>
      <PageHead title="Resum i decisió"
        question={<>Pregunta: <b>quina política hem d'enviar al leaderboard i quant marge de millora queda?</b> Tots els valors corresponen a: <b>{period.label}</b>.</>}
        right={<span className="chip warn">TRAIN · no és el test ocult</span>} />

      <div className="banner">
        <div className="icon">{Icon.bulb}</div>
        <div>
          <h3>Recomanació: {best ? <>enviar <u>{best.a.label}</u> (score {fmt(best.m.score)})</> : "—"}</h3>
          <p>
            {isFinite(ceiling) && best && <>Captura el <b>{fmt(pctCeil(best.m.score), 0)}%</b> del sostre teòric ({fmt(ceiling)} pts amb informació perfecta): queden <b>{fmt(ceiling - best.m.score)} punts</b> per guanyar. </>}
            {weakMonth && <>El forat més gran de <b>{main.label}</b> respecte de l'òptim és al mes de <b>{monthLabel(weakMonth.key)}</b> ({fmt(weakMonth.gap)} pts). </>}
            {best && best.m.infr > 0 && <b>Atenció: té {best.m.infr} infraccions. </b>}
          </p>
        </div>
        <div className="actions">
          <button className="btn" onClick={() => c.goTo("potencial")}>On perdem punts</button>
          <button className="btn primary" onClick={() => c.goTo("lab")}>Provar millores</button>
        </div>
      </div>

      <div className="grid g-5" style={{ marginBottom: 16 }}>
        <Kpi label={<AgentTag a={main} />} value={fmt(mm.score)} unit="pts" foot={<><Delta v={mm.score - cm.score} /> vs {cmp.label}</>} />
        <Kpi label="Reducció CO₂ (pes 70%)" value={fmt(mm.co2Pct)} unit="%" foot={<><span>{fmtInt(mm.co2SavedKg)} kg evitats</span><Delta v={mm.co2Pct - cm.co2Pct} unit=" pp" /></>} />
        <Kpi label="Estalvi econòmic (pes 30%)" value={fmt(mm.costPct)} unit="%" foot={<><span>{fmtInt(mm.costSavedEur)} € estalviats</span><Delta v={mm.costPct - cm.costPct} unit=" pp" /></>} />
        <Kpi label="Infraccions físiques" value={fmtInt(mm.infr)} chip={mm.infr === 0 ? <span className="chip ok">{Icon.check} segur</span> : <span className="chip bad">penalitza</span>}
          foot={<span>{mm.infr ? `−${fmt(opts.penaltyPts * mm.infr)} pts` : "cap penalització"} ({fmt(opts.penaltyPts)} pts per infracció)</span>} />
        <Kpi label="Captura del sostre teòric" value={isFinite(ceiling) ? fmt(pctCeil(mm.score), 0) : "—"} unit="%"
          foot={<div style={{ width: "100%" }}><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(0, Math.min(100, pctCeil(mm.score)))}%` }} /></div><span className="note">sostre = {fmt(ceiling)} pts (òptim amb informació perfecta)</span></div>} />
      </div>

      <div className="grid g-2" style={{ marginBottom: 16 }}>
        <Card title="Rànquing de polítiques i composició del score" sub="Cada barra suma 0,7 × reducció de CO₂ + 0,3 × estalvi de cost − penalitzacions. Clica una barra per fer-la agent principal."
          how={<><b>Decisió:</b> el CO₂ pesa més del doble que el cost. Una política que només persegueix preus barats deixa punts sobre la taula.</>}>
          <Chart option={rankOpt as any} height={Math.max(240, ranking.length * 44 + 40)} onEvents={{ click: (p) => { const r = ranking[p.dataIndex]; if (r) c.setMain(r.a.id); } }} />
        </Card>
        <Card title="Trade-off CO₂ vs cost" sub="Cada punt és una política (rombe = no implementable). Les diagonals són línies d'iso-score."
          how={<><b>Decisió:</b> moure's cap a dalt a la dreta. Desplaçar-se horitzontalment (més CO₂) val 2,3 vegades més que verticalment (més cost).</>}>
          <Chart option={scatterOpt as any} height={320} onEvents={{ click: (p) => { if (p.data?.id) c.setMain(p.data.id); } }} />
        </Card>
      </div>

      <div className="grid g-21">
        <Card title="On es guanyen els punts al llarg del temps" sub="Contribució acumulada al score. Si la línia es manté plana, la bateria no aporta res en aquelles hores; si baixa, empitjora el baseline."
          how={<><b>Decisió:</b> busqueu els trams en què la distància amb l'òptim (línia discontínua) s'eixampla i obriu-los a «Operació».</>}>
          <Chart option={cumOpt as any} height={330} />
        </Card>
        <Card title="Posició al leaderboard públic" sub={lb ? lb.note : "Sense dades de leaderboard"}>
          {lb ? <LeaderboardPanel c={c} v1Train={v1?.m.score} /> : <p className="note">Afegeix public/leaderboard.json.</p>}
        </Card>
      </div>
    </>
  );
}

function LeaderboardPanel({ c, v1Train }: { c: AppCtx; v1Train?: number }) {
  const lb = c.d.leaderboard!;
  const last = lb.submissions[lb.submissions.length - 1];
  const gap = lb.leader ? lb.leader.score - last.score : NaN;
  const k = c.k;
  const opt = {
    ...baseOption(k),
    grid: { left: 10, right: 30, top: 10, bottom: 10, containLabel: true },
    tooltip: { ...baseOption(k).tooltip, trigger: "axis", axisPointer: { type: "shadow" }, valueFormatter: (v: number) => fmt(v) + " pts" },
    xAxis: axis(k, { type: "value", max: 8 }),
    yAxis: axis(k, { type: "category", inverse: true, data: ["Nostre v1 · train local", "Nostre v1 · test públic", "Líder visible · test públic"] }),
    series: [{ type: "bar", barWidth: 16, data: [
      { value: v1Train ?? 0, itemStyle: { color: k.muted } },
      { value: last.score, itemStyle: { color: k.load } },
      { value: lb.leader?.score ?? 0, itemStyle: { color: k.accent } },
    ], label: { show: true, position: "right", color: k.ink, fontWeight: 700, formatter: (p: any) => fmt(p.value) } }],
  };
  return (
    <div className="stack" style={{ gap: 10 }}>
      <div style={{ display: "flex", gap: 24, alignItems: "baseline" }}>
        <div><div className="note">Darrera tramesa ({last.time})</div><div className="big-number">{fmt(last.score)}</div></div>
        <div><div className="note">Distància al líder</div><div className="big-number" style={{ color: "var(--bad)" }}>−{fmt(gap)}</div></div>
        <div><div className="note">Posició</div><div style={{ fontWeight: 700, fontSize: 16 }}>{last.rank}</div></div>
      </div>
      <Chart option={opt as any} height={140} />
      <div className="kv">
        <span>ΔCO₂ / ΔCost (nostre)</span><span>{fmt(last.co2_pct)}% · {fmt(last.cost_pct)}%</span>
        {lb.leader && <><span>ΔCO₂ / ΔCost (líder)</span><span>{fmt(lb.leader.co2_pct)}% · {fmt(lb.leader.cost_pct)}%</span></>}
      </div>
      <p className="note" style={{ margin: 0 }}>Font: {lb.source}. Les setmanes de test (darrers 7 dies de cada mes) no són les del train: no compareu directament amb el sostre del train.</p>
    </div>
  );
}

export type { Agent };
