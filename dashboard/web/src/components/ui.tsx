import type { ReactNode } from "react";
import type { Agent, Dataset, Period } from "../data";
import type { ScoreOpts } from "../sim";
import type { Tokens } from "../theme";

export interface AppCtx {
  d: Dataset;
  agents: Agent[];
  main: Agent;
  cmp: Agent;
  period: Period;
  opts: ScoreOpts;
  k: Tokens;
  setMain: (id: string) => void;
  setCmp: (id: string) => void;
  goTo: (tab: string, week?: string) => void;
  focusWeek: string | null;
  addAgent: (a: Agent) => void;
  removeAgent: (id: string) => void;
}

export function Card({ title, sub, how, right, children, style }: {
  title?: ReactNode; sub?: ReactNode; how?: ReactNode; right?: ReactNode; children: ReactNode; style?: React.CSSProperties;
}) {
  return (
    <section className="card" style={style}>
      {(title || right) && (
        <div className="card-head">
          <div>
            {title && <h3>{title}</h3>}
            {sub && <div className="sub">{sub}</div>}
          </div>
          {right}
        </div>
      )}
      {children}
      {how && <div className="how">{how}</div>}
    </section>
  );
}

export function Delta({ v, d = 2, unit = "", invert = false }: { v: number; d?: number; unit?: string; invert?: boolean }) {
  const good = invert ? v < 0 : v > 0;
  const cls = Math.abs(v) < 0.5 * 10 ** -d ? "flat" : good ? "up" : "down";
  const s = (v > 0 ? "+" : v < 0 ? "−" : "±") + Math.abs(v).toLocaleString("ca-ES", { minimumFractionDigits: d, maximumFractionDigits: d });
  return <span className={`delta ${cls}`}>{s}{unit}</span>;
}

export function Kpi({ label, value, unit, foot, chip }: { label: ReactNode; value: ReactNode; unit?: string; foot?: ReactNode; chip?: ReactNode }) {
  return (
    <div className="card kpi">
      <div className="label"><span>{label}</span>{chip}</div>
      <div className="value">{value}{unit && <small>{unit}</small>}</div>
      {foot && <div className="foot">{foot}</div>}
    </div>
  );
}

export function PageHead({ title, question, right }: { title: string; question: ReactNode; right?: ReactNode }) {
  return (
    <div className="page-head">
      <div>
        <h2>{title}</h2>
        <div className="question">{question}</div>
      </div>
      {right}
    </div>
  );
}

export function Seg<T extends string | number>({ value, options, onChange }: { value: T; options: { v: T; l: string }[]; onChange: (v: T) => void }) {
  return (
    <div className="seg" role="group">
      {options.map((o) => (
        <button key={String(o.v)} className={o.v === value ? "on" : ""} onClick={() => onChange(o.v)} aria-pressed={o.v === value}>{o.l}</button>
      ))}
    </div>
  );
}

export function Swatch({ color }: { color: string }) {
  return <span className="swatch" style={{ background: color }} />;
}

export function AgentTag({ a }: { a: Agent }) {
  return <span><Swatch color={a.color} />{a.label}</span>;
}

export const Icon = {
  battery: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><rect x="2" y="7" width="17" height="10" rx="2" /><path d="M22 11v2" /><path d="M6 10v4M10 10v4" /></svg>,
  bulb: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V16h8v-1.3A7 7 0 0 0 12 2z" /></svg>,
  sun: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>,
  moon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>,
  check: <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M20 6 9 17l-5-5" /></svg>,
};
