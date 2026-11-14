import { useMemo } from "react";
import { energyFlows, fmt, fmtInt, hourlyContribution, type Agent } from "../data";
import { axis, baseOption } from "../theme";
import { Chart } from "../components/Chart";
import { AgentTag, Card, Kpi, PageHead, type AppCtx } from "../components/ui";

export function Potencial({ c }: { c: AppCtx }) {
  const { d, agents, main, cmp, period, opts, k } = c;
  const mask = period.mask;
  const oracle = agents.find((a) => a.id === "oracle") ?? cmp;
  const fm = useMemo(() => energyFlows(d, main, mask), [d, main, mask]);
  const fc = useMemo(() => energyFlows(d, cmp, mask), [d, cmp, mask]);

  const sankey = (a: Agent, f: ReturnType<typeof energyFlows>) => {
    const links = [
      { source: "Xarxa", target: "Bateria", value: f.gridToBatt },
      { source: "Excedent solar", target: "Bateria", value: f.solarToBatt },
      { source: "Xarxa", target: "Pèrdues de conversió", value: f.chargeLoss },
      { source: "Bateria", target: "Campus (demanda)", value: f.battToCampus },
      { source: "Bateria", target: "Abocat (0 €)", value: f.battToExport },
      { source: "Bateria", target: "Pèrdues de conversió", value: f.dischargeLoss },
    ].filter((l) => l.value > 0.5);
    const colors: Record<string, string> = {
      "Xarxa": k.grid_import, "Excedent solar": k.pv, "Bateria": a.color, "Campus (demanda)": k.accent,
      "Abocat (0 €)": k.muted, "Pèrdues de conversió": k.bad,
    };
    const used = new Set(links.flatMap((l) => [l.source, l.target]));
    return {
      ...baseOption(k),
      tooltip: { ...baseOption(k).tooltip, trigger: "item", formatter: (p: any) => p.dataType === "edge" ? `${p.data.source} → ${p.data.target}: <b>${fmtInt(p.data.value)} kWh</b>` : `${p.name}: <b>${fmtInt(p.value)} kWh</b>` },
      series: [{
        type: "sankey", left: 10, right: 150, top: 10, bottom: 10, nodeWidth: 12, nodeGap: 14, draggable: false,
        label: { color: k.ink2, fontSize: 12, formatter: (p: any) => `${p.name}
${fmtInt(p.value)} kWh` }, lineStyle: { color: "gradient", opacity: 0.35 },
        data: Object.keys(colors).filter((n) => used.has(n)).map((name) => ({ name, itemStyle: { color: colors[name] } })),
        links,
      }],
    };
  };

  const gapHourOpt = useMemo(() => {
    const cm = hourlyContribution(d, main, opts, mask);
    const co = hourlyContribution(d, oracle, opts, mask);
    const accM = new Array(24).fill(0), accO = new Array(24).fill(0);
    for (let t = 0; t < d.t.length; t++) { if (mask && !mask[t]) continue; accM[d.hour[t]] += cm[t]; accO[d.hour[t]] += co[t]; }
    return {
      ...baseOption(k),
      grid: { left: 50, right: 16, top: 60, bottom: 30 },
      tooltip: { ...baseOption(k).tooltip, trigger: "axis", valueFormatter: (v: number) => fmt(v, 3) + " pts" },
      xAxis: axis(k, { type: "category", data: Array.from({ length: 24 }, (_, h) => `${h}h`) }),
      yAxis: axis(k, { type: "value", name: "punts aportats" }),
      series: [
        { name: main.label, type: "bar", data: accM.map((v) => +v.toFixed(4)), itemStyle: { color: main.color } },
        { name: oracle.label, type: "bar", data: accO.map((v) => +v.toFixed(4)), itemStyle: { color: oracle.color, opacity: 0.6 } },
        { name: "Bretxa (òptim − principal)", type: "line", data: accO.map((v, h) => +(v - accM[h]).toFixed(4)), lineStyle: { color: k.bad, width: 2 }, itemStyle: { color: k.bad }, symbol: "circle", symbolSize: 5 },
      ],
    };
  }, [d, main, oracle, opts, mask, k]);

  const socOpt = useMemo(() => {
    const bins = 10;
    const h = (a: Agent) => {
      const arr = new Array(bins).fill(0);
      let n = 0;
      for (let t = 0; t < d.t.length; t++) { if (mask && !mask[t]) continue; arr[Math.min(bins - 1, Math.floor((a.soc[t] / 2000) * bins))]++; n++; }
      return arr.map((x) => +((100 * x) / n).toFixed(1));
    };
    return {
      ...baseOption(k),
      grid: { left: 46, right: 16, top: 60, bottom: 40 },
      tooltip: { ...baseOption(k).tooltip, trigger: "axis", valueFormatter: (v: number) => fmt(v, 1) + "% de les hores" },
      xAxis: axis(k, { type: "category", data: Array.from({ length: bins }, (_, i) => `${i * 10}–${i * 10 + 10}%`), name: "SOC", nameLocation: "middle", nameGap: 26 }),
      yAxis: axis(k, { type: "value", name: "% hores" }),
      series: [main, cmp].map((a, i) => ({ name: a.label, type: "bar", data: h(a), itemStyle: { color: a.color, opacity: i ? 0.55 : 1 } })),
    };
  }, [d, main, cmp, mask, k]);

  const wastePct = (f: typeof fm) => (f.battToCampus + f.battToExport > 0 ? (100 * f.battToExport) / (f.battToCampus + f.battToExport) : 0);
  const days = fm.hours / 24;

  return (
    <>
      <PageHead title="Pèrdues i potencial"
        question={<>Pregunta: <b>on es perd energia i punts, i quin és el sostre real que podem assolir?</b> Compara <AgentTag a={main} /> amb <AgentTag a={cmp} />.</>} />
      <div className="grid g-5" style={{ marginBottom: 16 }}>
        <Kpi label="Cicles equivalents" value={fmt(fm.cycles, 0)} foot={<span>{fmt(fm.cycles / days, 2)} cicles/dia · {cmp.label}: {fmt(fc.cycles / days, 2)}</span>} />
        <Kpi label="Pèrdues de conversió" value={fmtInt(fm.chargeLoss + fm.dischargeLoss)} unit="kWh" foot={<span>{cmp.label}: {fmtInt(fc.chargeLoss + fc.dischargeLoss)} kWh</span>} />
        <Kpi label="Descàrrega abocada" value={fmt(wastePct(fm), 1)} unit="%" chip={wastePct(fm) > 2 ? <span className="chip warn">malbaratament</span> : <span className="chip ok">ok</span>}
          foot={<span>{fmtInt(fm.battToExport)} kWh descarregats sense demanda (0 €/kWh)</span>} />
        <Kpi label="Hores amb la bateria buida" value={fmt((100 * fm.hoursEmpty) / fm.hours, 1)} unit="%" foot={<span>{cmp.label}: {fmt((100 * fc.hoursEmpty) / fc.hours, 1)}%</span>} />
        <Kpi label="Hores amb la bateria plena" value={fmt((100 * fm.hoursFull) / fm.hours, 1)} unit="%" foot={<span>{cmp.label}: {fmt((100 * fc.hoursFull) / fc.hours, 1)}%</span>} />
      </div>
      <div className="grid g-2" style={{ marginBottom: 16 }}>
        <Card title={<>Fluxos d'energia · <AgentTag a={main} /></>} sub="D'on ve l'energia que entra a la bateria i on va a parar (kWh en el període)"
          how={<><b>Decisió:</b> l'energia abocada no té valor (exportació a 0 €); limitar la descàrrega a la demanda del campus és un guany gairebé gratuït.</>}>
          <Chart option={sankey(main, fm) as any} height={300} />
        </Card>
        <Card title={<>Fluxos d'energia · <AgentTag a={cmp} /></>} sub="Mateix diagrama per a la política de comparació">
          <Chart option={sankey(cmp, fc) as any} height={300} />
        </Card>
      </div>
      <div className="grid g-2">
        <Card title="On es perden els punts: aportació per hora del dia" sub={<>Punts de score que aporta cada hora del dia, sumats en tot el període · {main.label} vs {oracle.label}</>}
          how={<><b>Decisió:</b> els pics de la línia vermella marquen les franges horàries on més punts es poden recuperar. És on cal centrar la millora de la política.</>}>
          <Chart option={gapHourOpt as any} height={320} />
        </Card>
        <Card title="Distribució de l'estat de càrrega" sub="Percentatge d'hores en cada tram de SOC"
          how={<><b>Com llegir-ho:</b> moltes hores a 0% abans dels pics vol dir que la política descarrega massa d'hora; moltes hores a 100% amb sol vol dir que no queda espai per absorbir l'excedent solar.</>}>
          <Chart option={socOpt as any} height={320} />
        </Card>
      </div>
    </>
  );
}
