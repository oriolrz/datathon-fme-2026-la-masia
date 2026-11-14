import { useDeferredValue, useMemo, useState } from "react";
import { agentMetrics, fmt, fmtInt, nextColor, unique, type Agent } from "../data";
import {
  metrics, OFFICIAL_SPEC, RANK_DEFAULT, rankPolicy, simulate, thresholdPolicy, V1_PARAMS,
  type Policy, type RankParams, type ScoreOpts, type Spec, type ThresholdParams,
} from "../sim";
import { axis, baseOption } from "../theme";
import { Chart } from "../components/Chart";
import { AgentTag, Card, Delta, Kpi, PageHead, Seg, type AppCtx } from "../components/ui";

type Family = "threshold" | "rank";

interface SliderDef { key: string; label: string; min: number; max: number; step: number; hint: string; fmt?: (v: number) => string }

const T_SLIDERS: SliderDef[] = [
  { key: "wCo2", label: "Pes intern del CO₂", min: 0, max: 1, step: 0.05, hint: "0 = només preu · 1 = només CO₂ (no és el 70/30 del score)" },
  { key: "threshold", label: "Llindar de desviació", min: 0, max: 0.6, step: 0.01, hint: "Com de lluny de la mitjana de les 24 h ha d'estar l'hora per actuar" },
  { key: "margin", label: "Marge d'arbitratge", min: 0, max: 0.4, step: 0.01, hint: "Guany mínim exigit després del 10% de pèrdues" },
  { key: "power", label: "Potència de consigna", min: 50, max: 500, step: 10, hint: "kW que es demanen quan s'actua", fmt: (v) => `${v} kW` },
];
const R_SLIDERS: SliderDef[] = [
  { key: "wCo2", label: "Pes intern del CO₂", min: 0, max: 1, step: 0.05, hint: "0 = només preu · 1 = només CO₂" },
  { key: "kCharge", label: "Hores de càrrega (k)", min: 1, max: 12, step: 1, hint: "Carrega si l'hora és entre les k més netes/barates de les 24 visibles" },
  { key: "kDischarge", label: "Hores de descàrrega (k)", min: 1, max: 12, step: 1, hint: "Descarrega si és entre les k més cares/brutes" },
  { key: "minSpread", label: "Diferència mínima", min: 0, max: 0.5, step: 0.01, hint: "Separació mínima de valor per justificar un cicle" },
  { key: "power", label: "Potència de consigna", min: 50, max: 500, step: 10, hint: "kW que es demanen quan s'actua", fmt: (v) => `${v} kW` },
];

let labCounter = 1;

export function Laboratori({ c }: { c: AppCtx }) {
  const { d, agents, opts, period, k } = c;
  const [family, setFamily] = useState<Family>("threshold");
  const [tp, setTp] = useState<ThresholdParams>(V1_PARAMS);
  const [rp, setRp] = useState<RankParams>(RANK_DEFAULT);
  const [spec, setSpec] = useState<Spec>(OFFICIAL_SPEC);
  const [exportPrice, setExportPrice] = useState(0);
  const [sweepKey, setSweepKey] = useState<string>("threshold");
  const [sizing, setSizing] = useState<{ cap: number; score: number }[] | null>(null);
  const [copied, setCopied] = useState(false);

  const labOpts: ScoreOpts = useMemo(() => ({ ...opts, exportPrice }), [opts, exportPrice]);
  const params = family === "threshold" ? tp : rp;
  const dParams = useDeferredValue(params);
  const dSpec = useDeferredValue(spec);
  const mkPolicy = (f: Family, p: any): Policy => (f === "threshold" ? thresholdPolicy(p) : rankPolicy(p));

  const sim = useMemo(() => simulate(d.s, dSpec, mkPolicy(family, dParams)), [d, dSpec, family, dParams]);
  const m = useMemo(() => metrics(d.s, sim.applied, sim.infr, period.mask, labOpts), [sim, d, period, labOpts]);
  const v1 = agents.find((a) => a.id === "oriol_v1");
  const oracle = agents.find((a) => a.id === "oracle");
  const mv1 = v1 ? agentMetrics(d, v1, labOpts, period.mask) : null;
  const mor = oracle ? agentMetrics(d, oracle, labOpts, period.mask) : null;
  const isOfficialSpec = spec.capacity === 2000 && spec.power === 500 && spec.efficiency === 0.9;

  const split = useMemo(() => {
    const months = unique(d.month);
    const A = new Set(months.filter((_, i) => i % 2 === 0));
    const mA = Uint8Array.from(d.month, (x) => (A.has(x) ? 1 : 0));
    const mB = Uint8Array.from(d.month, (x) => (A.has(x) ? 0 : 1));
    const a = metrics(d.s, sim.applied, sim.infr, mA, labOpts).score;
    const b = metrics(d.s, sim.applied, sim.infr, mB, labOpts).score;
    const va = v1 ? agentMetrics(d, v1, labOpts, mA).score : 0;
    const vb = v1 ? agentMetrics(d, v1, labOpts, mB).score : 0;
    return { a, b, va, vb };
  }, [sim, d, labOpts, v1]);

  const sliders = family === "threshold" ? T_SLIDERS : R_SLIDERS;
  const setParam = (key: string, v: number | boolean) => {
    if (family === "threshold") setTp({ ...tp, [key]: v }); else setRp({ ...rp, [key]: v });
  };

  const sweep = useMemo(() => {
    const def = sliders.find((s) => s.key === sweepKey) ?? sliders[0];
    const n = 21;
    const xs = Array.from({ length: n }, (_, i) => +(def.min + ((def.max - def.min) * i) / (n - 1)).toFixed(4));
    const ys = xs.map((x) => {
      const p = { ...dParams, [def.key]: def.step >= 1 ? Math.round(x) : x };
      const r = simulate(d.s, dSpec, mkPolicy(family, p));
      return +metrics(d.s, r.applied, r.infr, period.mask, labOpts).score.toFixed(3);
    });
    return { def, xs, ys };
  }, [sweepKey, family, dParams, dSpec, d, period, labOpts]);

  const sweepOpt = {
    ...baseOption(k),
    grid: { left: 46, right: 16, top: 20, bottom: 40 },
    tooltip: { ...baseOption(k).tooltip, trigger: "axis", valueFormatter: (v: number) => fmt(v) + " pts" },
    xAxis: axis(k, { type: "category", data: sweep.xs.map((x) => fmt(x, sweep.def.step >= 1 ? 0 : 2)), name: sweep.def.label, nameLocation: "middle", nameGap: 26 }),
    yAxis: axis(k, { type: "value", name: "score", scale: true }),
    series: [
      { type: "line", data: sweep.ys, smooth: true, symbolSize: 6, lineStyle: { color: k.accent, width: 2.4 }, itemStyle: { color: k.accent }, areaStyle: { color: k.accent, opacity: 0.08 },
        markLine: { symbol: "none", silent: true, data: [
          ...(mv1 ? [{ yAxis: +mv1.score.toFixed(3), lineStyle: { color: v1!.color, type: "dashed" }, label: { formatter: "v1", color: v1!.color } }] : []),
          { xAxis: fmt(sweep.xs.reduce((b, x) => (Math.abs(x - (params as any)[sweep.def.key]) < Math.abs(b - (params as any)[sweep.def.key]) ? x : b), sweep.xs[0]), sweep.def.step >= 1 ? 0 : 2), lineStyle: { color: k.muted }, label: { formatter: "actual", color: k.muted } },
        ] } },
    ],
  };

  const runSizing = () => {
    const caps = [500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000];
    setSizing(caps.map((cap) => {
      const sp = { ...spec, capacity: cap, power: spec.power };
      const r = simulate(d.s, sp, mkPolicy(family, params));
      return { cap, score: metrics(d.s, r.applied, r.infr, period.mask, labOpts).score };
    }));
  };
  const sizingOpt = sizing && {
    ...baseOption(k),
    grid: { left: 46, right: 16, top: 20, bottom: 40 },
    tooltip: { ...baseOption(k).tooltip, trigger: "axis", valueFormatter: (v: number) => fmt(v) + " pts" },
    xAxis: axis(k, { type: "category", data: sizing.map((s) => `${fmt(s.cap / 1000, 1)} MWh`), name: `capacitat (potència ${spec.power} kW)`, nameLocation: "middle", nameGap: 26 }),
    yAxis: axis(k, { type: "value", name: "score" }),
    series: [{ type: "bar", data: sizing.map((s) => ({ value: +s.score.toFixed(3), itemStyle: { color: s.cap === 2000 ? k.accent : k.load, opacity: s.cap === 2000 ? 1 : 0.6 } })), barMaxWidth: 34,
      label: { show: true, position: "top", color: k.ink2, fontSize: 11, formatter: (p: any) => fmt(p.value, 1) } }],
  };

  const save = () => {
    const id = `lab_${labCounter++}`;
    const a: Agent = {
      id, label: `Lab ${id.slice(4)} · ${family === "threshold" ? "llindars" : "rànquing"}`, custom: true,
      description: `Creat al laboratori: ${JSON.stringify(params)}${isOfficialSpec ? "" : ` · bateria ${JSON.stringify(spec)}`}`,
      owner: "Laboratori", kind: "laboratori", source: "navegador (simulador TS verificat)", implementable: true,
      color: nextColor(agents.map((x) => x.color)), applied: sim.applied, requested: sim.requested, soc: sim.soc.map((s) => (s / spec.capacity) * 2000), infr: sim.infr,
      params: { family, ...params, spec },
    };
    c.addAgent(a);
    c.setMain(id);
  };

  const copy = async () => {
    const txt = JSON.stringify({ family, params, spec, exportPrice, score_train: +m.score.toFixed(3) }, null, 2);
    try { await navigator.clipboard.writeText(txt); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { /* sense porta-retalls */ }
  };

  const custom = agents.filter((a) => a.custom);

  return (
    <>
      <PageHead title="Laboratori what-if"
        question={<>Pregunta: <b>quina millora val la pena enviar, i quina part del resultat depèn de la bateria o dels supòsits?</b> Cada canvi torna a simular les 5.993 hores al navegador amb el mateix model físic que environment.py (verificat: v1 = 4,26).</>}
        right={<span className="chip info">Simulació en directe · {period.label}</span>} />
      <div className="grid g-lab">
        <Card>
          <div className="section-title">Família de política</div>
          <Seg value={family} onChange={setFamily} options={[{ v: "threshold", l: "Llindars 24 h (v1)" }, { v: "rank", l: "Rànquing 24 h" }]} />
          <p className="note">{family === "threshold"
            ? "Mateixa lògica que src/fallback.py: compara el valor de l'hora actual amb la mitjana de les 24 h visibles."
            : "Carrega a les k hores més netes i barates de les 24 h visibles i descarrega a les k més cares i brutes."}</p>
          <div className="section-title">Paràmetres</div>
          {sliders.map((s) => {
            const v = (params as any)[s.key] as number;
            return (
              <label key={s.key} className="slider">
                <div className="row"><span>{s.label}</span><b>{s.fmt ? s.fmt(v) : fmt(v, s.step >= 1 ? 0 : 2)}</b></div>
                <input type="range" min={s.min} max={s.max} step={s.step} value={v} onChange={(e) => setParam(s.key, +e.target.value)} />
                <span className="hint">{s.hint}</span>
              </label>
            );
          })}
          <label className="toggle"><input type="checkbox" checked={(params as any).capToDemand} onChange={(e) => setParam("capToDemand", e.target.checked)} />
            Limitar la descàrrega a la demanda neta de l'hora anterior</label>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" onClick={() => (family === "threshold" ? setTp(V1_PARAMS) : setRp(RANK_DEFAULT))}>Restableix</button>
          </div>

          <div className="section-title">Bateria (decisió d'inversió UPC)</div>
          <Slider label="Capacitat" v={spec.capacity} min={500} max={6000} step={250} f={(v) => `${fmtInt(v)} kWh`} on={(v) => setSpec({ ...spec, capacity: v })} />
          <Slider label="Potència de l'inversor" v={spec.power} min={100} max={1500} step={50} f={(v) => `${v} kW`} on={(v) => setSpec({ ...spec, power: v })} />
          <Slider label="Rendiment de cicle" v={spec.efficiency} min={0.8} max={0.98} step={0.01} f={(v) => `${Math.round(v * 100)}%`} on={(v) => setSpec({ ...spec, efficiency: v })} />
          {!isOfficialSpec && <button className="btn" onClick={() => setSpec(OFFICIAL_SPEC)}>Torna a la bateria oficial</button>}

          <div className="section-title">Supòsits del reglament</div>
          <label className="toggle"><input type="checkbox" checked={exportPrice > 0} onChange={(e) => setExportPrice(e.target.checked ? 0.04 : 0)} />
            Remunerar l'exportació a 0,04 €/kWh (discrepància de la web)</label>
          <p className="note">La penalització per infracció es tria a la capçalera (ara {fmt(opts.penaltyPts)} pts).</p>
        </Card>

        <div className="stack">
          <div className="grid g-3">
            <Kpi label="Score de la variant" value={fmt(m.score)} unit="pts"
              foot={<>{mv1 && <><Delta v={m.score - mv1.score} /> vs v1</>}{!isOfficialSpec && <span className="chip warn">bateria no oficial</span>}</>} />
            <Kpi label="ΔCO₂ · ΔCost" value={`${fmt(m.co2Pct)} · ${fmt(m.costPct)}`} unit="%" foot={<span>{fmtInt(m.co2SavedKg)} kg · {fmtInt(m.costSavedEur)} €</span>} />
            <Kpi label="Captura del sostre" value={mor && isOfficialSpec ? fmt((100 * m.score) / mor.score, 0) : "—"} unit={mor && isOfficialSpec ? "%" : ""}
              chip={m.infr ? <span className="chip bad">{m.infr} infr.</span> : <span className="chip ok">0 infr.</span>}
              foot={<span>{mor ? `òptim teòric ${fmt(mor.score)} pts` : ""}{!isOfficialSpec ? " (només amb la bateria oficial)" : ""}</span>} />
          </div>
          <Card title="Validació anti-sobreajust" sub="Score als mesos alterns (A = set, des, feb, abr, jun, ago · B = la resta). Una millora real ha de guanyar a totes dues meitats.">
            <div className="kv" style={{ gridTemplateColumns: "1fr auto auto auto" }}>
              <span></span><span className="note">Variant</span><span className="note">v1</span><span className="note">Δ</span>
              <span>Meitat A</span><span>{fmt(split.a)}</span><span>{fmt(split.va)}</span><span><Delta v={split.a - split.va} /></span>
              <span>Meitat B</span><span>{fmt(split.b)}</span><span>{fmt(split.vb)}</span><span><Delta v={split.b - split.vb} /></span>
            </div>
            <p className="note" style={{ marginBottom: 0 }}>
              {split.a > split.va && split.b > split.vb ? "✔ Millora consistent a totes dues meitats: és candidata per al dry-run de 48 h."
                : split.a > split.va || split.b > split.vb ? "⚠ Només millora en una de les meitats: risc de sobreajust. No consumiu cap tramesa."
                : "✖ No millora la v1 en cap meitat."}
            </p>
          </Card>
          <div className="grid g-2">
            <Card title="Sensibilitat" sub="Score segons el paràmetre triat, amb la resta fixos"
              right={<select value={sweepKey} onChange={(e) => setSweepKey(e.target.value)} aria-label="Paràmetre a escombrar">{sliders.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}</select>}
              how={<><b>Decisió:</b> trieu valors on la corba és plana (estables). Un pic estret és sobreajust al train.</>}>
              <Chart option={sweepOpt as any} height={260} />
            </Card>
            <Card title="Dimensionament de la bateria" sub="Score segons la capacitat, amb aquesta política i la potència actual"
              right={<button className="btn" onClick={runSizing}>Calcula</button>}
              how={<><b>Per a UPC Sostenible:</b> com creix el benefici si s'instal·len més MWh? Si el guany decreix, ampliar la potència pot valer més que ampliar la capacitat.</>}>
              {sizingOpt ? <Chart option={sizingOpt as any} height={260} /> : <div className="loading" style={{ height: 260 }}>Prem «Calcula» (9 simulacions)</div>}
            </Card>
          </div>
          <Card title="Exportar la variant" sub="Afegiu-la a totes les vistes del dashboard o passeu els paràmetres a l'Oriol i al Dani">
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn primary" onClick={save}>Desa com a agent i compara-la</button>
              <button className="btn" onClick={copy}>{copied ? "Copiat ✓" : "Copia els paràmetres (JSON)"}</button>
            </div>
            {custom.length > 0 && (
              <table className="t" style={{ marginTop: 12 }}>
                <thead><tr><th>Variant desada</th><th className="num">Score</th><th></th></tr></thead>
                <tbody>{custom.map((a) => (
                  <tr key={a.id}><td><AgentTag a={a} /></td><td className="num">{fmt(agentMetrics(d, a, opts, period.mask).score)}</td>
                    <td className="num"><button className="btn" onClick={() => c.removeAgent(a.id)}>Elimina</button></td></tr>
                ))}</tbody>
              </table>
            )}
            <p className="note" style={{ marginBottom: 0 }}>Les variants només existeixen en aquesta sessió del navegador. Per enviar-ne una, cal implementar-la a <span className="mono">agent.py</span> i passar els tests de l'Oriol.</p>
          </Card>
        </div>
      </div>
    </>
  );
}

function Slider({ label, v, min, max, step, f, on }: { label: string; v: number; min: number; max: number; step: number; f: (v: number) => string; on: (v: number) => void }) {
  return (
    <label className="slider">
      <div className="row"><span>{label}</span><b>{f(v)}</b></div>
      <input type="range" min={min} max={max} step={step} value={v} onChange={(e) => on(+e.target.value)} />
    </label>
  );
}
