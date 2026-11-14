// Port exacte a TypeScript de starter_kit/environment.py (CampusBatteryEnv) i de
// evaluate_results. Permet el laboratori «what-if» al navegador.
// `npm run verify-sim` comprova que reprodueix el resultat oficial de l'agent v1.
// Sense imports: el pot executar Node directament (type stripping).

export interface Series {
  load: number[];
  pv: number[];
  price: number[];
  co2: number[];
}

export interface Spec {
  capacity: number; // kWh
  power: number; // kW
  efficiency: number; // rendiment de cicle (0.9)
  socInit: number; // fracció
}

export const OFFICIAL_SPEC: Spec = { capacity: 2000, power: 500, efficiency: 0.9, socInit: 0.5 };

export interface ScoreOpts {
  alpha: number;
  beta: number;
  penaltyPts: number; // punts per infracció (0.2 codi, 1.0 enunciat)
  exportPrice: number; // €/kWh
}

export const OFFICIAL_SCORE: ScoreOpts = { alpha: 0.7, beta: 0.3, penaltyPts: 0.2, exportPrice: 0 };

export interface Ctx {
  t: number;
  n: number;
  soc: number;
  s: Series;
  spec: Spec;
}

export type Policy = (c: Ctx) => number;

export interface SimResult {
  requested: Float64Array;
  applied: Float64Array;
  soc: Float64Array;
  infr: Int8Array;
}

/** Reproducció pas a pas de CampusBatteryEnv.step */
export function simulate(s: Series, spec: Spec, policy: Policy): SimResult {
  const n = s.load.length;
  const cap = spec.capacity;
  const pmax = spec.power;
  const eta = Math.sqrt(spec.efficiency);
  let soc = spec.socInit * cap;
  const requested = new Float64Array(n);
  const applied = new Float64Array(n);
  const socArr = new Float64Array(n);
  const infr = new Int8Array(n);
  const ctx: Ctx = { t: 0, n, soc, s, spec };
  for (let t = 0; t < n; t++) {
    ctx.t = t;
    ctx.soc = soc;
    const req = policy(ctx);
    requested[t] = req;
    let k = 0;
    const p = Math.min(pmax, Math.max(-pmax, req));
    if (p !== req) k++;
    let pa = 0;
    if (p > 0) {
      const maxC = (cap - soc) / eta;
      pa = Math.min(p, Math.max(0, maxC));
      if (pa < p) k++;
      soc += pa * eta;
    } else if (p < 0) {
      const maxD = soc * eta;
      pa = -Math.min(-p, Math.max(0, maxD));
      if (pa > p) k++;
      soc += pa / eta;
    }
    if (soc < -1e-6 || soc > cap + 1e-6) k++;
    soc = Math.min(cap, Math.max(0, soc));
    applied[t] = pa;
    socArr[t] = soc;
    infr[t] = k;
  }
  return { requested, applied, soc: socArr, infr };
}

export interface Metrics {
  score: number;
  scoreRaw: number; // sense max(0, ·)
  co2Pct: number;
  costPct: number;
  co2SavedKg: number;
  costSavedEur: number;
  co2BaseKg: number;
  costBaseEur: number;
  infr: number;
  hours: number;
}

/** Mateixa fórmula que evaluate_results (opcionalment amb màscara temporal). */
export function metrics(
  s: Series,
  applied: ArrayLike<number>,
  infr: ArrayLike<number> | null,
  mask: ArrayLike<number | boolean> | null = null,
  o: ScoreOpts = OFFICIAL_SCORE,
): Metrics {
  let cost = 0, em = 0, cb = 0, eb = 0, nInf = 0, h = 0;
  const n = s.load.length;
  for (let t = 0; t < n; t++) {
    if (mask && !mask[t]) continue;
    h++;
    const net0 = s.load[t] - s.pv[t];
    const net = net0 + applied[t];
    const g = net > 0 ? net : 0;
    const x = net < 0 ? -net : 0;
    const b = net0 > 0 ? net0 : 0;
    cost += g * s.price[t] - x * o.exportPrice;
    em += g * s.co2[t];
    cb += b * s.price[t];
    eb += b * s.co2[t];
    if (infr) nInf += infr[t];
  }
  const dCo2 = eb > 0 ? (eb - em) / eb : 0;
  const dCost = cb > 0 ? (cb - cost) / cb : 0;
  const raw = (o.alpha * dCo2 + o.beta * dCost) * 100 - o.penaltyPts * nInf;
  return {
    score: Math.max(0, raw), scoreRaw: raw, co2Pct: dCo2 * 100, costPct: dCost * 100,
    co2SavedKg: eb - em, costSavedEur: cb - cost, co2BaseKg: eb, costBaseEur: cb, infr: nInf, hours: h,
  };
}

/** Límits físics amb marge (mateix clamp que src/safety.py de l'equip). */
export function clampAction(a: number, soc: number, spec: Spec, eps = 1e-4): number {
  const eta = Math.sqrt(spec.efficiency);
  const hi = Math.max(0, Math.min(spec.power, (spec.capacity - soc) / eta - eps));
  const lo = -Math.max(0, Math.min(spec.power, soc * eta - eps));
  return Math.max(lo, Math.min(hi, a));
}

// ------------------------------------------------------------------ polítiques
function windowValues(c: Ctx, wCo2: number): number[] | null {
  const end = Math.min(c.t + 24, c.n);
  const m = end - c.t;
  if (m < 3) return null;
  let mp = 0, mc = 0;
  for (let i = c.t; i < end; i++) { mp += c.s.price[i]; mc += c.s.co2[i]; }
  mp /= m; mc /= m;
  if (mp <= 1e-9 || mc <= 1e-9) return null;
  const v = new Array<number>(m);
  for (let i = 0; i < m; i++) {
    v[i] = wCo2 * c.s.co2[c.t + i] / (mc + 1e-9) + (1 - wCo2) * c.s.price[c.t + i] / (mp + 1e-9);
  }
  return v;
}

/** Límit opcional: no descarregar més del que el campus consumia l'hora anterior (evita abocar). */
function demandCap(c: Ctx): number {
  const t = c.t > 0 ? c.t - 1 : 0;
  return Math.max(0, c.s.load[t] - c.s.pv[t]);
}

export interface ThresholdParams {
  wCo2: number; threshold: number; margin: number; power: number; capToDemand: boolean;
}

/** Política «Llindars 24h» — idèntica a src/fallback.py (La MasIA v1) amb els paràmetres per defecte. */
export const V1_PARAMS: ThresholdParams = { wCo2: 0.5, threshold: 0.2, margin: 0.05, power: 500, capToDemand: false };

export function thresholdPolicy(p: ThresholdParams): Policy {
  return (c) => {
    const v = windowValues(c, p.wCo2);
    if (!v) return 0;
    const cur = v[0];
    let mean = 0, mx = -Infinity, mn = Infinity;
    for (const x of v) { mean += x; if (x > mx) mx = x; if (x < mn) mn = x; }
    mean /= v.length;
    const eff = c.spec.efficiency;
    let a = 0;
    if (cur < mean - p.threshold && mx > cur / eff + p.margin) a = p.power;
    else if (cur > mean + p.threshold && mn < eff * cur - p.margin) a = -p.power;
    if (a < 0 && p.capToDemand) a = -Math.min(-a, demandCap(c));
    return clampAction(a, c.soc, c.spec);
  };
}

export interface RankParams {
  wCo2: number; kCharge: number; kDischarge: number; minSpread: number; power: number; capToDemand: boolean;
}

export const RANK_DEFAULT: RankParams = { wCo2: 0.7, kCharge: 5, kDischarge: 5, minSpread: 0.15, power: 500, capToDemand: true };

/** Política «Rànquing 24h»: carrega a les k hores més netes/barates i descarrega a les k més cares. */
export function rankPolicy(p: RankParams): Policy {
  return (c) => {
    const v = windowValues(c, p.wCo2);
    if (!v) return 0;
    const cur = v[0];
    let below = 0, above = 0, mx = -Infinity, mn = Infinity;
    for (let i = 1; i < v.length; i++) {
      if (v[i] < cur) below++;
      if (v[i] > cur) above++;
      if (v[i] > mx) mx = v[i];
      if (v[i] < mn) mn = v[i];
    }
    const eff = c.spec.efficiency;
    let a = 0;
    if (below < p.kCharge && mx > cur / eff + p.minSpread) a = p.power;
    else if (above < p.kDischarge && mn < cur * eff - p.minSpread) a = -p.power;
    if (a < 0 && p.capToDemand) a = -Math.min(-a, demandCap(c));
    return clampAction(a, c.soc, c.spec);
  };
}
