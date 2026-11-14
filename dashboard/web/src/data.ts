import { metrics, type Metrics, type ScoreOpts, type Series } from "./sim";

export interface RawAgent {
  id: string; label: string; description: string; owner: string; kind: string; source: string;
  implementable: boolean; color: string; runtime_s: number;
  official: Record<string, number>;
  requested: number[]; applied: number[]; soc: number[]; infr_idx: number[]; infr_n: number[];
}

export interface Agent {
  id: string; label: string; description: string; owner: string; kind: string; source: string;
  implementable: boolean; color: string; runtime_s?: number;
  official?: Record<string, number>;
  applied: Float64Array; requested: Float64Array; soc: Float64Array; infr: Int8Array;
  custom?: boolean; params?: Record<string, unknown>;
}

export interface Meta {
  generated_at: string; git_commit: string; git_branch: string; environment_sha256: string;
  dataset: string; dataset_note: string; hours: number; start: string; end: string;
  blocks: { i0: number; i1: number; start: string; end: string; hours: number }[];
  spec: Record<string, number>; discrepancies: string[];
}

export interface Leaderboard {
  updated: string; source: string; note: string;
  submissions: { time: string; label: string; score: number; co2_pct: number; cost_pct: number; infr: number; rank?: string; agent_id?: string }[];
  leader?: { score: number; co2_pct: number; cost_pct: number; note: string };
}

export interface Dataset {
  meta: Meta;
  s: Series;
  t: string[];
  month: string[]; // YYYY-MM
  week: string[]; // YYYY-MM-Sn
  day: string[]; // YYYY-MM-DD
  hour: Int8Array;
  dow: Int8Array;
  w: Float64Array; // pes marginal oficial per kWh importat (normalitzat a mitjana 1)
  agents: Agent[];
  leaderboard: Leaderboard | null;
}

const PALETTE = ["#2f6fed", "#e0621b", "#8b5cf6", "#0ea5a4", "#d9468c", "#6b8e23"];

export function toAgent(r: RawAgent, n: number): Agent {
  const infr = new Int8Array(n);
  r.infr_idx.forEach((i, k) => (infr[i] = r.infr_n[k]));
  return {
    id: r.id, label: r.label, description: r.description, owner: r.owner, kind: r.kind, source: r.source,
    implementable: r.implementable, color: r.color, runtime_s: r.runtime_s, official: r.official,
    applied: Float64Array.from(r.applied), requested: Float64Array.from(r.requested), soc: Float64Array.from(r.soc), infr,
  };
}

export function nextColor(used: string[]): string {
  return PALETTE.find((c) => !used.includes(c)) ?? PALETTE[used.length % PALETTE.length];
}

export async function loadDataset(): Promise<Dataset> {
  const get = async (p: string) => {
    const r = await fetch(p);
    if (!r.ok) throw new Error(`${p}: ${r.status}`);
    return r.json();
  };
  const [meta, base, raw] = await Promise.all([get("data/meta.json"), get("data/base.json"), get("data/agents.json")]);
  let leaderboard: Leaderboard | null = null;
  try { leaderboard = await get("leaderboard.json"); } catch { /* opcional */ }
  const t: string[] = base.t;
  const n = t.length;
  const s: Series = { load: base.load, pv: base.pv, price: base.price, co2: base.co2 };
  const month = t.map((x) => x.slice(0, 7));
  const day = t.map((x) => x.slice(0, 10));
  const week = t.map((x) => {
    const d = +x.slice(8, 10);
    return `${x.slice(0, 7)}-S${d <= 7 ? 1 : d <= 14 ? 2 : d <= 21 ? 3 : 4}`;
  });
  const hour = Int8Array.from(t, (x) => +x.slice(11, 13));
  const dow = Int8Array.from(t, (x) => (new Date(x.slice(0, 10) + "T12:00:00Z").getUTCDay() + 6) % 7);
  let eb = 0, cb = 0;
  for (let i = 0; i < n; i++) {
    const b = Math.max(0, s.load[i] - s.pv[i]);
    eb += b * s.co2[i]; cb += b * s.price[i];
  }
  const w = new Float64Array(n);
  let mw = 0;
  for (let i = 0; i < n; i++) { w[i] = 0.7 * s.co2[i] / eb + 0.3 * s.price[i] / cb; mw += w[i]; }
  mw /= n;
  for (let i = 0; i < n; i++) w[i] /= mw;
  const agents = (raw as RawAgent[]).map((r, i) => {
    const a = toAgent(r, n);
    if (!a.color) a.color = PALETTE[i % PALETTE.length];
    return a;
  });
  return { meta, s, t, month, week, day, hour, dow, w, agents, leaderboard };
}

// ------------------------------------------------------------------ períodes
export interface Period { id: string; label: string; mask: Uint8Array | null }

const MONTHS_CA = ["gen", "feb", "mar", "abr", "mai", "jun", "jul", "ago", "set", "oct", "nov", "des"];
export const monthLabel = (m: string) => `${MONTHS_CA[+m.slice(5, 7) - 1]} ${m.slice(2, 4)}`;
export const weekLabel = (w: string) => `${monthLabel(w.slice(0, 7))} · ${w.slice(8)}`;
export const SEASON: Record<string, string> = {
  "01": "hivern", "02": "hivern", "12": "hivern", "03": "primavera", "04": "primavera", "05": "primavera",
  "06": "estiu", "07": "estiu", "08": "estiu", "09": "tardor", "10": "tardor", "11": "tardor",
};

export function periods(d: Dataset): Period[] {
  const out: Period[] = [{ id: "all", label: "Tot el train (5.993 h)", mask: null }];
  const seasons = ["tardor", "hivern", "primavera", "estiu"];
  for (const se of seasons) {
    const m = Uint8Array.from(d.month, (x) => (SEASON[x.slice(5, 7)] === se ? 1 : 0));
    out.push({ id: `s:${se}`, label: `Estació · ${se}`, mask: m });
  }
  const months = unique(d.month);
  for (const mo of months) out.push({ id: `m:${mo}`, label: `Mes · ${monthLabel(mo)}`, mask: Uint8Array.from(d.month, (x) => (x === mo ? 1 : 0)) });
  out.push({ id: "wd", label: "Només dies laborables", mask: Uint8Array.from(d.dow, (x) => (x < 5 ? 1 : 0)) });
  out.push({ id: "we", label: "Només caps de setmana", mask: Uint8Array.from(d.dow, (x) => (x >= 5 ? 1 : 0)) });
  return out;
}

export function unique<T>(a: T[]): T[] {
  return Array.from(new Set(a));
}

// ------------------------------------------------------------------ agregacions
export interface GroupStat { key: string; hours: number; score: number; scoreRaw: number; co2Pct: number; costPct: number; infr: number }

/** KPI per grup (setmana, mes, dia…) en una sola passada; la base és la de cada grup, com evaluate_results(mask). */
export function groupMetrics(d: Dataset, a: Agent, keys: string[], opts: ScoreOpts, mask: Uint8Array | null = null): GroupStat[] {
  const acc = new Map<string, { h: number; em: number; eb: number; c: number; cb: number; inf: number }>();
  const s = d.s;
  for (let t = 0; t < keys.length; t++) {
    if (mask && !mask[t]) continue;
    const net0 = s.load[t] - s.pv[t];
    const net = net0 + a.applied[t];
    const g = Math.max(0, net), x = Math.max(0, -net), b = Math.max(0, net0);
    let r = acc.get(keys[t]);
    if (!r) { r = { h: 0, em: 0, eb: 0, c: 0, cb: 0, inf: 0 }; acc.set(keys[t], r); }
    r.h++; r.em += g * s.co2[t]; r.eb += b * s.co2[t]; r.c += g * s.price[t] - x * opts.exportPrice; r.cb += b * s.price[t]; r.inf += a.infr[t];
  }
  return Array.from(acc, ([key, r]) => {
    const dc = r.eb > 0 ? (r.eb - r.em) / r.eb : 0;
    const dk = r.cb > 0 ? (r.cb - r.c) / r.cb : 0;
    const raw = (opts.alpha * dc + opts.beta * dk) * 100 - opts.penaltyPts * r.inf;
    return { key, hours: r.h, score: Math.max(0, raw), scoreRaw: raw, co2Pct: dc * 100, costPct: dk * 100, infr: r.inf };
  });
}

export function agentMetrics(d: Dataset, a: Agent, opts: ScoreOpts, mask: Uint8Array | null): Metrics {
  return metrics(d.s, a.applied, a.infr, mask, opts);
}

/** Contribució acumulada al score (punts) al llarg del període. */
export function cumulativeScore(d: Dataset, a: Agent, opts: ScoreOpts, mask: Uint8Array | null): number[] {
  const s = d.s;
  let eb = 0, cb = 0;
  for (let t = 0; t < s.load.length; t++) {
    if (mask && !mask[t]) continue;
    const b = Math.max(0, s.load[t] - s.pv[t]);
    eb += b * s.co2[t]; cb += b * s.price[t];
  }
  const out: number[] = [];
  let acc = 0;
  for (let t = 0; t < s.load.length; t++) {
    if (mask && !mask[t]) continue;
    const net0 = s.load[t] - s.pv[t];
    const net = net0 + a.applied[t];
    const g = Math.max(0, net), x = Math.max(0, -net), b = Math.max(0, net0);
    acc += 100 * (opts.alpha * (b - g) * s.co2[t] / eb + opts.beta * ((b - g) * s.price[t] + x * opts.exportPrice) / cb) - opts.penaltyPts * a.infr[t];
    out.push(acc);
  }
  return out;
}

/** Contribució al score per hora (punts), per desglossar on es guanya o es perd. */
export function hourlyContribution(d: Dataset, a: Agent, opts: ScoreOpts, mask: Uint8Array | null): Float64Array {
  const s = d.s;
  let eb = 0, cb = 0;
  for (let t = 0; t < s.load.length; t++) {
    if (mask && !mask[t]) continue;
    const b = Math.max(0, s.load[t] - s.pv[t]);
    eb += b * s.co2[t]; cb += b * s.price[t];
  }
  const out = new Float64Array(s.load.length);
  for (let t = 0; t < s.load.length; t++) {
    if (mask && !mask[t]) continue;
    const net0 = s.load[t] - s.pv[t];
    const net = net0 + a.applied[t];
    const g = Math.max(0, net), x = Math.max(0, -net), b = Math.max(0, net0);
    out[t] = 100 * (opts.alpha * (b - g) * s.co2[t] / eb + opts.beta * ((b - g) * s.price[t] + x * opts.exportPrice) / cb) - opts.penaltyPts * a.infr[t];
  }
  return out;
}

export interface EnergyFlows {
  gridToBatt: number; solarToBatt: number; chargeLoss: number; battToCampus: number; battToExport: number;
  dischargeLoss: number; throughput: number; cycles: number; hoursEmpty: number; hoursFull: number; hoursIdle: number; hours: number;
}

export function energyFlows(d: Dataset, a: Agent, mask: Uint8Array | null, eff = 0.9, cap = 2000): EnergyFlows {
  const eta = Math.sqrt(eff);
  const s = d.s;
  const f: EnergyFlows = { gridToBatt: 0, solarToBatt: 0, chargeLoss: 0, battToCampus: 0, battToExport: 0, dischargeLoss: 0, throughput: 0, cycles: 0, hoursEmpty: 0, hoursFull: 0, hoursIdle: 0, hours: 0 };
  for (let t = 0; t < s.load.length; t++) {
    if (mask && !mask[t]) continue;
    f.hours++;
    const p = a.applied[t];
    const net0 = s.load[t] - s.pv[t];
    if (p > 0.01) {
      const surplus = Math.max(0, -net0);
      const fromSolar = Math.min(p, surplus);
      f.solarToBatt += fromSolar * eta; f.gridToBatt += (p - fromSolar) * eta; f.chargeLoss += p * (1 - eta);
      f.throughput += p;
    } else if (p < -0.01) {
      const q = -p;
      const demand = Math.max(0, net0);
      f.battToCampus += Math.min(q, demand); f.battToExport += Math.max(0, q - demand);
      f.dischargeLoss += q / eta - q;
      f.throughput += q;
    } else f.hoursIdle++;
    if (a.soc[t] <= cap * 0.01) f.hoursEmpty++;
    if (a.soc[t] >= cap * 0.99) f.hoursFull++;
  }
  f.cycles = f.throughput / 2 / cap;
  return f;
}

export function quantiles(v: number[]) {
  const a = [...v].sort((x, y) => x - y);
  const q = (p: number) => {
    const i = (a.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
    return a[lo] + (a[hi] - a[lo]) * (i - lo);
  };
  const q1 = q(0.25), q2 = q(0.5), q3 = q(0.75), iqr = q3 - q1;
  const lf = q1 - 1.5 * iqr, uf = q3 + 1.5 * iqr;
  const inside = a.filter((x) => x >= lf && x <= uf);
  return { q1, q2, q3, iqr, lf, uf, min: inside[0] ?? q1, max: inside[inside.length - 1] ?? q3, mean: a.reduce((x, y) => x + y, 0) / a.length };
}

// ------------------------------------------------------------------ format
const nf = (d: number) => new Intl.NumberFormat("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
export const fmt = (x: number, d = 2) => nf(d).format(x);
export const fmtInt = (x: number) => nf(0).format(x);
export const signed = (x: number, d = 2) => (x > 0 ? "+" : x < 0 ? "−" : "±") + nf(d).format(Math.abs(x));
