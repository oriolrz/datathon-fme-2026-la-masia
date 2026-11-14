import { useEffect, useMemo, useState } from "react";
import { loadDataset, periods, type Agent, type Dataset } from "./data";
import { OFFICIAL_SCORE, type ScoreOpts } from "./sim";
import { tokens } from "./theme";
import { Icon, type AppCtx } from "./components/ui";
import { Resum } from "./views/Resum";
import { Operacio } from "./views/Operacio";
import { Patrons } from "./views/Patrons";
import { Robustesa } from "./views/Robustesa";
import { Potencial } from "./views/Potencial";
import { Laboratori } from "./views/Laboratori";

const TABS = [
  { id: "resum", label: "Resum i decisió" },
  { id: "operacio", label: "Operació hora a hora" },
  { id: "patrons", label: "Patrons" },
  { id: "robustesa", label: "Robustesa · Tukey" },
  { id: "potencial", label: "Pèrdues i potencial" },
  { id: "lab", label: "Laboratori what-if" },
];

function readHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  return { tab: h.get("tab") ?? "resum", main: h.get("a"), cmp: h.get("b"), period: h.get("p") };
}

function safeGet(key: string) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function safeSet(key: string, v: string) {
  try { localStorage.setItem(key, v); } catch { /* sense emmagatzematge */ }
}

export function App() {
  const [d, setD] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const init = readHash();
  const [tab, setTab] = useState(init.tab);
  const [mainId, setMainId] = useState<string | null>(init.main);
  const [cmpId, setCmpId] = useState<string | null>(init.cmp);
  const [periodId, setPeriodId] = useState(init.period ?? "all");
  const [penalty, setPenalty] = useState<number>(0.2);
  const [custom, setCustom] = useState<Agent[]>([]);
  const [focusWeek, setFocusWeek] = useState<string | null>(null);
  const [dark, setDark] = useState<boolean>(() => {
    const s = safeGet("bdl-theme");
    return s ? s === "dark" : window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });

  useEffect(() => { loadDataset().then(setD).catch((e) => setError(String(e))); }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    safeSet("bdl-theme", dark ? "dark" : "light");
  }, [dark]);

  const agents = useMemo(() => (d ? [...d.agents, ...custom] : []), [d, custom]);
  const pers = useMemo(() => (d ? periods(d) : []), [d]);
  const k = useMemo(() => tokens(dark), [dark]);
  const opts: ScoreOpts = useMemo(() => ({ ...OFFICIAL_SCORE, penaltyPts: penalty }), [penalty]);

  const defMain = agents.find((a) => a.id === "oriol_v1") ?? agents.find((a) => a.implementable && a.id !== "standby") ?? agents[0];
  const main = agents.find((a) => a.id === mainId) ?? defMain;
  const cmp = agents.find((a) => a.id === cmpId) ?? agents.find((a) => a.id === "oracle") ?? agents[0];
  const period = pers.find((p) => p.id === periodId) ?? pers[0];

  useEffect(() => {
    if (!main) return;
    const h = new URLSearchParams({ tab, a: main.id, b: cmp.id, p: period?.id ?? "all" });
    history.replaceState(null, "", `#${h}`);
  }, [tab, main?.id, cmp?.id, period?.id]);

  if (error) return (
    <div className="err card">
      <h3>No s'han pogut carregar les dades</h3>
      <p className="note">Executa primer el pipeline des de l'arrel del repositori:</p>
      <pre className="mono">python -m dashboard.pipeline.build</pre>
      <p className="note">{error}</p>
    </div>
  );
  if (!d || !main) return <div className="loading">Carregant simulacions…</div>;

  const ctx: AppCtx = {
    d, agents, main, cmp, period, opts, k,
    setMain: setMainId, setCmp: setCmpId,
    goTo: (t, w) => { setTab(t); if (w) setFocusWeek(w); window.scrollTo({ top: 0, behavior: "smooth" }); },
    focusWeek,
    addAgent: (a) => { setCustom((c) => [...c.filter((x) => x.id !== a.id), a]); },
    removeAgent: (id) => { setCustom((c) => c.filter((x) => x.id !== id)); if (mainId === id) setMainId(null); if (cmpId === id) setCmpId(null); },
  };

  const agentOptions = agents.map((a) => <option key={a.id} value={a.id}>{a.label}{a.custom ? " · lab" : ""}</option>);

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand-row">
            <div className="brand">
              <div className="brand-mark">{Icon.battery}</div>
              <div>
                <h1>Battery Decision Lab</h1>
                <p>La MasIA · Repte UPC Sostenible · Datathon FME 2026</p>
              </div>
            </div>
            <div className="controls">
              <label className="field"><span>Agent principal</span>
                <select value={main.id} onChange={(e) => setMainId(e.target.value)} aria-label="Agent principal">{agentOptions}</select>
              </label>
              <label className="field"><span>Comparar amb</span>
                <select value={cmp.id} onChange={(e) => setCmpId(e.target.value)} aria-label="Agent de comparació">{agentOptions}</select>
              </label>
              <label className="field"><span>Període</span>
                <select value={period.id} onChange={(e) => setPeriodId(e.target.value)} aria-label="Període">
                  {pers.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
              </label>
              <label className="field" title="environment.py resta 0,20 punts per infracció; l'enunciat diu 1,00">
                <span>Penalització</span>
                <select value={penalty} onChange={(e) => setPenalty(+e.target.value)} aria-label="Penalització per infracció">
                  <option value={0.2}>0,20 / infr. (codi)</option>
                  <option value={1}>1,00 / infr. (enunciat)</option>
                </select>
              </label>
              <button className="iconbtn" onClick={() => setDark(!dark)} aria-label="Canvia el tema" title="Tema clar/fosc">{dark ? Icon.sun : Icon.moon}</button>
            </div>
          </div>
          <nav className="tabs" role="tablist">
            {TABS.map((t, i) => (
              <button key={t.id} role="tab" aria-selected={tab === t.id} className={`tab ${tab === t.id ? "active" : ""}`} onClick={() => setTab(t.id)}>
                <span className="num">{i + 1}</span>{t.label}
              </button>
            ))}
          </nav>
        </div>
      </header>
      <main>
        {tab === "resum" && <Resum c={ctx} />}
        {tab === "operacio" && <Operacio c={ctx} />}
        {tab === "patrons" && <Patrons c={ctx} />}
        {tab === "robustesa" && <Robustesa c={ctx} />}
        {tab === "potencial" && <Potencial c={ctx} />}
        {tab === "lab" && <Laboratori c={ctx} />}
        <footer className="footer">
          <span><b>Dades:</b> {d.meta.dataset_note}</span>
          <span>Generat {new Date(d.meta.generated_at).toLocaleString("ca-ES")} · commit <span className="mono">{d.meta.git_commit}</span> · environment.py <span className="mono">{d.meta.environment_sha256}</span></span>
          <span>Tots els KPI es recalculen amb la fórmula de <span className="mono">evaluate_results</span> i es verifiquen contra el simulador oficial.</span>
        </footer>
      </main>
    </>
  );
}
