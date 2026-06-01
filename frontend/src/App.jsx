import { useState, useEffect, useRef } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from "recharts";

// ─── Mock data (replace with FastAPI calls in production) ────────────────────
const PAIN_THEMES = [
  { theme: "Onboarding friction", frequency: 14, severity: 8.4, segment: "SMB" },
  { theme: "Slow report generation", frequency: 11, severity: 7.9, segment: "Enterprise" },
  { theme: "Missing API docs", frequency: 9, severity: 6.2, segment: "Developer" },
  { theme: "Mobile experience gaps", frequency: 8, severity: 5.8, segment: "SMB" },
  { theme: "Export limitations", frequency: 6, severity: 7.1, segment: "Enterprise" },
  { theme: "Notification overload", frequency: 5, severity: 4.3, segment: "All" },
];

const EVAL_HISTORY = [
  { day: "Day 1", hallucination: 18.4, confidence: 61, trust: 54 },
  { day: "Day 3", hallucination: 14.2, confidence: 67, trust: 61 },
  { day: "Day 5", hallucination: 10.8, confidence: 71, trust: 68 },
  { day: "Day 7", hallucination: 7.3, confidence: 76, trust: 74 },
  { day: "Day 9", hallucination: 5.1, confidence: 82, trust: 81 },
  { day: "Day 11", hallucination: 3.9, confidence: 85, trust: 84 },
];

const DECISIONS = [
  { id: "D-012", feature: "AI report summariser", verdict: "GO", confidence: 87, date: "Jun 1", escalated: false, reasoning: "Low hallucination rate (3.9%), strong persona scores, EU AI Act: limited risk." },
  { id: "D-011", feature: "Predictive churn model", verdict: "NO-GO", confidence: 71, date: "May 30", escalated: true, reasoning: "Confidence stayed below threshold after two Reflexion passes. Escalated to human." },
  { id: "D-010", feature: "Auto email drafter", verdict: "GO", confidence: 81, date: "May 28", escalated: false, reasoning: "Faithfulness score 94%. Persona simulation: no compliance objections raised." },
  { id: "D-009", feature: "Customer sentiment feed", verdict: "GO", confidence: 78, date: "May 26", escalated: false, reasoning: "Hallucination rate 5.2%. Cost-per-decision within budget at $0.031." },
  { id: "D-008", feature: "Smart ticket router", verdict: "NO-GO", confidence: 63, date: "May 24", escalated: true, reasoning: "Bias detector flagged enterprise segment over-weighting. Governance module blocked." },
];

const COST_DATA = [
  { feature: "D-008", cost: 0.041 },
  { feature: "D-009", cost: 0.031 },
  { feature: "D-010", cost: 0.028 },
  { feature: "D-011", cost: 0.047 },
  { feature: "D-012", cost: 0.023 },
];

const ROUTING_POLICY = {
  default_model: "gpt-4o-mini",
  capable_model: "gpt-4o",
  threshold: 0.75,
  eligible_agents: ["orchestrator", "decider", "critic"],
  savings_estimate: "~90% cost reduction on eligible agents when confidence ≥ 0.75",
  breakdown: [
    { agent: "interview_agent",  model: "gpt-4o-mini", reason: "Discovery — low complexity" },
    { agent: "synthesis_agent",  model: "gpt-4o-mini", reason: "Extraction — low complexity" },
    { agent: "persona_agent",    model: "gpt-4o-mini", reason: "Simulation — low complexity" },
    { agent: "eval_agent",       model: "gpt-4o-mini", reason: "Scoring — structured output" },
    { agent: "governance",       model: "gpt-4o-mini", reason: "Classification — rule-based" },
    { agent: "orchestrator",     model: "gpt-4o → gpt-4o-mini", reason: "Upgrades when confidence < 0.75" },
    { agent: "decider",          model: "gpt-4o → gpt-4o-mini", reason: "Upgrades when confidence < 0.75" },
    { agent: "critic",           model: "gpt-4o → gpt-4o-mini", reason: "Upgrades when confidence < 0.75" },
  ]
};

const DRIFT_ALERTS = [
  { id: 1, metric: "Hallucination rate", delta: "+2.1pp", severity: "warning", time: "2h ago", feature: "AI report summariser" },
  { id: 2, metric: "Confidence calibration", delta: "-4.3pp", severity: "danger", time: "4h ago", feature: "Auto email drafter" },
  { id: 3, metric: "Trust score", delta: "+1.2pp", severity: "ok", time: "6h ago", feature: "Customer sentiment feed" },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
const SEGMENT_COLORS = { SMB: "#1D9E75", Enterprise: "#534AB7", Developer: "#D85A30", All: "#888780" };

function Badge({ children, type = "neutral" }) {
  const styles = {
    go: { background: "#E1F5EE", color: "#085041" },
    nogo: { background: "#FAECE7", color: "#712B13" },
    warning: { background: "#FAEEDA", color: "#633806" },
    danger: { background: "#FAECE7", color: "#712B13" },
    ok: { background: "#EAF3DE", color: "#27500A" },
    neutral: { background: "#F1EFE8", color: "#444441" },
    escalated: { background: "#EEEDFE", color: "#3C3489" },
  };
  const s = styles[type] || styles.neutral;
  return (
    <span style={{ ...s, fontSize: 11, fontWeight: 500, padding: "2px 8px", borderRadius: 6, display: "inline-block", whiteSpace: "nowrap" }}>
      {children}
    </span>
  );
}

function MetricCard({ label, value, sub, color }) {
  return (
    <div style={{ background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-md)", padding: "1rem", minWidth: 0 }}>
      <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 4px" }}>{label}</p>
      <p style={{ fontSize: 24, fontWeight: 500, color: color || "var(--color-text-primary)", margin: "0 0 2px" }}>{value}</p>
      {sub && <p style={{ fontSize: 11, color: "var(--color-text-tertiary)", margin: 0 }}>{sub}</p>}
    </div>
  );
}

function SectionHeader({ icon, title }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
      <i className={`ti ${icon}`} style={{ fontSize: 16, color: "var(--color-text-secondary)" }} aria-hidden="true" />
      <p style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.06em", margin: 0 }}>{title}</p>
    </div>
  );
}

// ─── Section: Pain Themes ─────────────────────────────────────────────────────
function PainThemesPanel() {
  const [sort, setSort] = useState("frequency");
  const sorted = [...PAIN_THEMES].sort((a, b) => b[sort] - a[sort]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <SectionHeader icon="ti-users" title="User pain themes — Stage 01 Discover" />
        <select value={sort} onChange={e => setSort(e.target.value)} style={{ fontSize: 12 }}>
          <option value="frequency">Sort by frequency</option>
          <option value="severity">Sort by severity</option>
        </select>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {sorted.map((t, i) => {
          const barW = Math.round((t.frequency / 14) * 100);
          return (
            <div key={t.theme} style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "10px 14px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>{t.theme}</span>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <Badge type="neutral">{t.segment}</Badge>
                  <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>sev {t.severity.toFixed(1)}</span>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ flex: 1, height: 4, background: "var(--color-background-secondary)", borderRadius: 2 }}>
                  <div style={{ width: `${barW}%`, height: "100%", background: SEGMENT_COLORS[t.segment] || "#888", borderRadius: 2 }} />
                </div>
                <span style={{ fontSize: 11, color: "var(--color-text-tertiary)", minWidth: 28, textAlign: "right" }}>{t.frequency}x</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Section: Eval Report Card ────────────────────────────────────────────────
function EvalPanel() {
  const latest = EVAL_HISTORY[EVAL_HISTORY.length - 1];

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-secondary)", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
        <p style={{ margin: "0 0 4px", fontWeight: 500 }}>{label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ margin: "2px 0", color: p.color }}>{p.name}: {p.value.toFixed(1)}{p.name === "hallucination" ? "%" : "%"}</p>
        ))}
      </div>
    );
  };

  return (
    <div>
      <SectionHeader icon="ti-microscope" title="Eval report card — Stage 02 Evaluate" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 }}>
        <MetricCard label="Hallucination rate" value={`${latest.hallucination}%`} sub="↓ 14.5pp since Day 1" color="#D85A30" />
        <MetricCard label="Confidence score" value={`${latest.confidence}%`} sub="↑ 24pp since Day 1" color="#1D9E75" />
        <MetricCard label="Trust score" value={`${latest.trust}%`} sub="↑ 30pp since Day 1" color="#534AB7" />
      </div>
      <div style={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={EVAL_HISTORY} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
            <XAxis dataKey="day" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="confidence" stroke="#1D9E75" strokeWidth={2} dot={false} name="confidence" />
            <Line type="monotone" dataKey="trust" stroke="#534AB7" strokeWidth={2} dot={false} name="trust" />
            <Line type="monotone" dataKey="hallucination" stroke="#D85A30" strokeWidth={2} dot={false} name="hallucination" strokeDasharray="4 2" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 12, color: "var(--color-text-secondary)" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 10, height: 2, background: "#1D9E75", display: "inline-block" }} />Confidence</span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 10, height: 2, background: "#534AB7", display: "inline-block" }} />Trust</span>
        <span style={{ display: "flex", alignItems: "center", gap: 4 }}><span style={{ width: 10, height: 2, borderTop: "2px dashed #D85A30", display: "inline-block" }} />Hallucination</span>
      </div>
    </div>
  );
}

// ─── Section: Decision History ────────────────────────────────────────────────
function DecisionPanel() {
  const [expanded, setExpanded] = useState(null);

  return (
    <div>
      <SectionHeader icon="ti-git-branch" title="Go / no-go decision history — Stage 03 Decide" />
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {DECISIONS.map(d => (
          <div key={d.id} style={{ background: "var(--color-background-primary)", border: `0.5px solid var(--color-border-tertiary)`, borderRadius: "var(--border-radius-md)", padding: "10px 14px", cursor: "pointer" }}
            onClick={() => setExpanded(expanded === d.id ? null : d.id)}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Badge type={d.verdict === "GO" ? "go" : "nogo"}>{d.verdict}</Badge>
                <span style={{ fontSize: 13, color: "var(--color-text-primary)" }}>{d.feature}</span>
                {d.escalated && <Badge type="escalated">escalated</Badge>}
              </div>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{d.confidence}% conf</span>
                <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>{d.date}</span>
                <i className={`ti ${expanded === d.id ? "ti-chevron-up" : "ti-chevron-down"}`} style={{ fontSize: 14, color: "var(--color-text-tertiary)" }} aria-hidden="true" />
              </div>
            </div>
            {expanded === d.id && (
              <div style={{ marginTop: 10, paddingTop: 10, borderTop: "0.5px solid var(--color-border-tertiary)", fontSize: 12, color: "var(--color-text-secondary)", lineHeight: 1.6 }}>
                <span style={{ fontWeight: 500, color: "var(--color-text-primary)" }}>{d.id} · Reasoning: </span>{d.reasoning}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Section: Cost per Decision + Routing Policy ─────────────────────────────
function CostPanel() {
  const avg = (COST_DATA.reduce((s, d) => s + d.cost, 0) / COST_DATA.length).toFixed(3);
  const total = COST_DATA.reduce((s, d) => s + d.cost, 0).toFixed(3);
  const [showRouting, setShowRouting] = useState(false);

  return (
    <div>
      <SectionHeader icon="ti-coin" title="Cost-per-decision — LLMOps" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 }}>
        <MetricCard label="Avg cost / decision" value={`$${avg}`} sub="gpt-4o-mini routing active" />
        <MetricCard label="Total pipeline cost" value={`$${total}`} sub="5 decisions to date" />
        <MetricCard label="Cost reduction" value="~90%" sub="vs always using gpt-4o" color="#1D9E75" />
      </div>
      <div style={{ height: 160 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={COST_DATA} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
            <XAxis dataKey="feature" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `$${v.toFixed(2)}`} />
            <Tooltip formatter={v => [`$${v.toFixed(3)}`, "Cost"]} />
            <ReferenceLine y={parseFloat(avg)} stroke="#534AB7" strokeDasharray="4 2" label={{ value: "avg", position: "right", fontSize: 10, fill: "#534AB7" }} />
            <Bar dataKey="cost" fill="#1D9E75" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Routing policy explainer */}
      <div style={{ marginTop: 16 }}>
        <button
          onClick={() => setShowRouting(!showRouting)}
          style={{ fontSize: 12, display: "flex", alignItems: "center", gap: 6, background: "transparent", border: "0.5px solid var(--color-border-secondary)", borderRadius: "var(--border-radius-md)", padding: "5px 12px", cursor: "pointer", color: "var(--color-text-primary)" }}>
          <i className={`ti ${showRouting ? "ti-chevron-up" : "ti-chevron-down"}`} style={{ fontSize: 12 }} />
          Model routing policy
        </button>

        {showRouting && (
          <div style={{ marginTop: 10, background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-md)", padding: "12px 14px" }}>
            <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 10px", lineHeight: 1.6 }}>
              <strong style={{ color: "var(--color-text-primary)" }}>Routing rule:</strong> All agents use <code>gpt-4o-mini</code> by default.
              Orchestrator, Decider, and Critic upgrade to <code>gpt-4o</code> only when aggregated confidence drops below <strong>0.75</strong>.
              This saves ~90% on inference costs while preserving quality on high-stakes decisions.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {ROUTING_POLICY.breakdown.map(r => (
                <div key={r.agent} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 12, padding: "4px 0", borderBottom: "0.5px solid var(--color-border-tertiary)" }}>
                  <span style={{ color: "var(--color-text-primary)", fontFamily: "monospace" }}>{r.agent}</span>
                  <span style={{ color: r.model.includes("→") ? "#D85A30" : "#1D9E75", fontWeight: 500 }}>{r.model}</span>
                  <span style={{ color: "var(--color-text-tertiary)", fontSize: 11 }}>{r.reason}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Section: Drift Alerts ────────────────────────────────────────────────────
function DriftPanel() {
  return (
    <div>
      <SectionHeader icon="ti-alert-triangle" title="Live drift alerts — Stage 04 Learn" />
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {DRIFT_ALERTS.map(a => (
          <div key={a.id} style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "10px 14px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <Badge type={a.severity}>{a.severity === "ok" ? "stable" : a.severity}</Badge>
              <div>
                <p style={{ margin: 0, fontSize: 13, color: "var(--color-text-primary)" }}>{a.metric} <span style={{ fontWeight: 500 }}>{a.delta}</span></p>
                <p style={{ margin: 0, fontSize: 11, color: "var(--color-text-secondary)" }}>{a.feature}</p>
              </div>
            </div>
            <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>{a.time}</span>
          </div>
        ))}
        <button style={{ marginTop: 4, fontSize: 12 }} onClick={() => alert("In production: calls FastAPI /learn endpoint to pull fresh ChromaDB metrics.")}>
          Refresh alerts ↗
        </button>
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState("discover");

  const tabs = [
    { id: "discover", label: "01 Discover", icon: "ti-users" },
    { id: "evaluate", label: "02 Evaluate", icon: "ti-microscope" },
    { id: "decide", label: "03 Decide", icon: "ti-git-branch" },
    { id: "learn", label: "04 Learn", icon: "ti-brain" },
  ];

  return (
    <div style={{ fontFamily: "var(--font-sans)", maxWidth: 860, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <h2 className="sr-only">AI Product Intelligence Loop dashboard</h2>

      {/* Header */}
      <div style={{ marginBottom: "1.5rem" }}>
        <p style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 4px" }}>AI Product Intelligence Loop</p>
        <h1 style={{ fontSize: 22, fontWeight: 500, margin: "0 0 6px" }}>Pipeline dashboard</h1>
        <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: 0 }}>Last run: today at 08:14 · 5 decisions logged · $0.170 total cost · 0 governance blocks</p>
      </div>

      {/* Summary metric row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: "1.5rem" }}>
        <MetricCard label="Interviews conducted" value="23" sub="Stage 01" />
        <MetricCard label="Hallucination rate" value="3.9%" sub="↓ from 18.4%" color="#D85A30" />
        <MetricCard label="Decisions this sprint" value="5" sub="3 GO · 2 NO-GO" />
        <MetricCard label="Cost per decision" value="$0.034" sub="60% below budget" color="#1D9E75" />
      </div>

      {/* Tab nav */}
      <div style={{ display: "flex", gap: 4, borderBottom: "0.5px solid var(--color-border-tertiary)", marginBottom: "1.5rem" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            style={{ background: "transparent", border: "none", borderBottom: activeTab === t.id ? "2px solid var(--color-text-primary)" : "2px solid transparent", padding: "6px 14px 8px", fontSize: 13, fontWeight: activeTab === t.id ? 500 : 400, color: activeTab === t.id ? "var(--color-text-primary)" : "var(--color-text-secondary)", cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
            <i className={`ti ${t.icon}`} style={{ fontSize: 14 }} aria-hidden="true" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === "discover" && <PainThemesPanel />}
        {activeTab === "evaluate" && <EvalPanel />}
        {activeTab === "decide" && <DecisionPanel />}
        {activeTab === "learn" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
            <CostPanel />
            <hr style={{ border: "none", borderTop: "0.5px solid var(--color-border-tertiary)" }} />
            <DriftPanel />
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{ marginTop: "2rem", paddingTop: "1rem", borderTop: "0.5px solid var(--color-border-tertiary)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>Stack: Python · OpenAI API · ChromaDB · FastAPI · React · n8n · Slack</span>
        <button style={{ fontSize: 12 }} onClick={() => alert("In production: POST to FastAPI /run-pipeline to trigger all 4 stages end-to-end.")}>
          Run full pipeline ↗
        </button>
      </div>
    </div>
  );
}
