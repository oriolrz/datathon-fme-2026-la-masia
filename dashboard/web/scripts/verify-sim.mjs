// Comprova que el simulador TypeScript del laboratori reprodueix el simulador oficial.
// Ús: npm run verify-sim   (després de python -m dashboard.pipeline.build)
import { readFileSync } from "node:fs";
import { simulate, metrics, thresholdPolicy, V1_PARAMS, OFFICIAL_SPEC } from "../src/sim.ts";

const dir = new URL("../public/data/", import.meta.url);
const base = JSON.parse(readFileSync(new URL("base.json", dir), "utf8"));
const agents = JSON.parse(readFileSync(new URL("agents.json", dir), "utf8"));
const s = { load: base.load, pv: base.pv, price: base.price, co2: base.co2 };

let ok = true;
// 1) Recàlcul dels KPI de cada agent a partir de la seva traça vs evaluate_results
for (const a of agents) {
  const infr = new Int8Array(base.t.length);
  a.infr_idx.forEach((i, k) => (infr[i] = a.infr_n[k]));
  const m = metrics(s, a.applied, infr);
  const d = Math.abs(m.score - a.official.score);
  const pass = d < 0.02 && m.infr === a.official.infraccions;
  ok &&= pass;
  console.log(`${pass ? "OK " : "ERR"} ${a.id.padEnd(18)} TS=${m.score.toFixed(2)} oficial=${a.official.score}`);
}
// 2) Simulació completa de la política v1 al navegador vs agent oriol_v1 oficial
const v1 = agents.find((a) => a.id === "oriol_v1");
if (v1) {
  const r = simulate(s, OFFICIAL_SPEC, thresholdPolicy(V1_PARAMS));
  const m = metrics(s, r.applied, r.infr);
  let maxDiff = 0;
  for (let t = 0; t < r.applied.length; t++) maxDiff = Math.max(maxDiff, Math.abs(r.applied[t] - v1.applied[t]));
  const pass = Math.abs(m.score - v1.official.score) < 0.02 && maxDiff < 0.05;
  ok &&= pass;
  console.log(`${pass ? "OK " : "ERR"} lab v1 TS score=${m.score.toFixed(3)} oficial=${v1.official.score} max|Δp|=${maxDiff.toFixed(4)} kW`);
}
process.exit(ok ? 0 : 1);
