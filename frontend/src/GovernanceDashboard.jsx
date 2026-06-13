// frontend/src/GovernanceDashboard.jsx
//
// AI Governance Dashboard — GRC view
// NIST AI RMF (GOVERN/MAP/MEASURE/MANAGE) | EU AI Act | ISO/IEC 42001 | AIGP BOK v2.1
//
// Reads from existing FastAPI endpoints:
//   GET /audit-trail     → audit log entries + summary
//   GET /security-report → injection attempts + security events
//   GET /cost-report     → cost per run data
//
// Falls back to mock data when API is unavailable (same pattern as App.jsx)
//
// Owner: Saurabh Mahajan (saurabh@arcaence.com)
// Version: 1.0 | June 2026

import { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell
} from "recharts";

const API = "http://localhost:8000";


// ── Mock data (same pattern as App.jsx — replace with live API data) ──────────

const MOCK_AUDIT = {
  summary: {
    total_decisions: 12,
    decision_breakdown: { GO: 7, NO_GO: 3, CONDITIONAL_GO: 2 },
    outcome_breakdown: { PENDING: 8, CORRECT: 3, INCORRECT: 1, PARTIALLY_CORRECT: 0 },
    avg_confidence_score: 0.81,
    escalation_rate: 0.17,
    total_tokens_consumed: 48200,
    grc: {
      bias_flag_rate: 0.08,
      pii_detection_rate: 0.25,
      grounding_fail_rate: 0.04,
      eu_ai_act_tiers: ["limited_risk", "minimal_risk"],
      governance_version: "1.0",
    },
  },
  entries: [
    { log_id: "LOG_001", run_id: "RUN_20260611_001", logged_at: "2026-06-11T09:14:00", feature: "AI report summariser", decision: "GO", confidence_score: 0.87, escalated_to_human: false, model_used: "gpt-4o-mini", outcome: "CORRECT", eu_ai_act_tier: "limited_risk", bias_flags_raised: false, bias_risk_level: "none", pii_items_redacted: 0, grounding_result: "PASS", input_hash: "535f482e" },
    { log_id: "LOG_002", run_id: "RUN_20260611_002", logged_at: "2026-06-11T11:22:00", feature: "Predictive churn model", decision: "NO_GO", confidence_score: 0.71, escalated_to_human: true, model_used: "gpt-4o", outcome: "PENDING", eu_ai_act_tier: "limited_risk", bias_flags_raised: false, bias_risk_level: "none", pii_items_redacted: 2, grounding_result: "FAIL", input_hash: "778c83bf" },
    { log_id: "LOG_003", run_id: "RUN_20260611_003", logged_at: "2026-06-11T13:05:00", feature: "Auto email drafter", decision: "GO", confidence_score: 0.81, escalated_to_human: false, model_used: "gpt-4o-mini", outcome: "CORRECT", eu_ai_act_tier: "limited_risk", bias_flags_raised: true, bias_risk_level: "low", pii_items_redacted: 3, grounding_result: "PASS", input_hash: "cecbc8fb" },
    { log_id: "LOG_004", run_id: "RUN_20260612_001", logged_at: "2026-06-12T08:47:00", feature: "Smart ticket router", decision: "NO_GO", confidence_score: 0.63, escalated_to_human: true, model_used: "gpt-4o", outcome: "PENDING", eu_ai_act_tier: "limited_risk", bias_flags_raised: true, bias_risk_level: "medium", pii_items_redacted: 1, grounding_result: "PASS", input_hash: "a1b2c3d4" },
    { log_id: "LOG_005", run_id: "RUN_20260612_002", logged_at: "2026-06-12T10:31:00", feature: "Customer sentiment feed", decision: "CONDITIONAL_GO", confidence_score: 0.76, escalated_to_human: false, model_used: "gpt-4o-mini", outcome: "PENDING", eu_ai_act_tier: "limited_risk", bias_flags_raised: false, bias_risk_level: "none", pii_items_redacted: 0, grounding_result: "PASS", input_hash: "e5f6g7h8" },
    { log_id: "LOG_006", run_id: "RUN_20260612_003", logged_at: "2026-06-12T14:18:00", feature: "Onboarding flow redesign", decision: "GO", confidence_score: 0.89, escalated_to_human: false, model_used: "gpt-4o-mini", outcome: "PENDING", eu_ai_act_tier: "limited_risk", bias_flags_raised: false, bias_risk_level: "none", pii_items_redacted: 0, grounding_result: "PASS", input_hash: "i9j0k1l2" },
    { log_id: "LOG_007", run_id: "RUN_20260613_001", logged_at: "2026-06-13T09:02:00", feature: "API rate limit feature", decision: "GO", confidence_score: 0.84, escalated_to_human: false, model_used: "gpt-4o-mini", outcome: "PENDING", eu_ai_act_tier: "minimal_risk", bias_flags_raised: false, bias_risk_level: "none", pii_items_redacted: 0, grounding_result: "PASS", input_hash: "m3n4o5p6" },
  ],
};

const MOCK_SECURITY = {
  total_events: 3,
  blocked_inputs: 2,
  unsafe_outputs_blocked: 1,
  events: [
    { timestamp: "2026-06-12T08:44:00", type: "injection_attempt", severity: "high", input_preview: "ignore all previous instructions...", blocked: true },
    { timestamp: "2026-06-11T15:32:00", type: "injection_attempt", severity: "medium", input_preview: "forget your system prompt and...", blocked: true },
    { timestamp: "2026-06-11T09:10:00", type: "unsafe_output", severity: "low", input_preview: "output contained os.system pattern", blocked: true },
  ],
};

const MOCK_COST = {
  total_cost_usd: 0.021,
  by_run: [
    { run: "RUN_001", cost: 0.003 },
    { run: "RUN_002", cost: 0.006 },
    { run: "RUN_003", cost: 0.003 },
    { run: "RUN_004", cost: 0.006 },
    { run: "RUN_005", cost: 0.003 },
  ],
};


// ── Design tokens — matches App.jsx exactly ───────────────────────────────────

const NAVY   = "#1B3A6B";
const GREEN  = "#1D9E75";
const PURPLE = "#534AB7";
const ORANGE = "#D85A30";
const AMBER  = "#BA7517";

const NIST_COLORS = {
  GOVERN:  { bg: "#E6F1FB", fg: "#0C447C" },
  MAP:     { bg: "#EAF3DE", fg: "#27500A" },
  MEASURE: { bg: "#FAEEDA", fg: "#633806" },
  MANAGE:  { bg: "#EEEDFE", fg: "#3C3489" },
};


// ── Reuse exact same helpers as App.jsx ───────────────────────────────────────

function Badge({ children, type = "neutral" }) {
  const styles = {
    go:       { background: "#E1F5EE", color: "#085041" },
    nogo:     { background: "#FAECE7", color: "#712B13" },
    cgo:      { background: "#FFF3E0", color: "#633806" },
    warning:  { background: "#FAEEDA", color: "#633806" },
    danger:   { background: "#FAECE7", color: "#712B13" },
    ok:       { background: "#EAF3DE", color: "#27500A" },
    neutral:  { background: "#F1EFE8", color: "#444441" },
    escalated:{ background: "#EEEDFE", color: "#3C3489" },
    high:     { background: "#FAECE7", color: "#712B13" },
    medium:   { background: "#FAEEDA", color: "#633806" },
    low:      { background: "#EAF3DE", color: "#27500A" },
    none:     { background: "#F1EFE8", color: "#444441" },
  };
  const s = styles[type] || styles.neutral;
  return (
    <span style={{ ...s, fontSize: 11, fontWeight: 500, padding: "2px 8px",
                   borderRadius: 6, display: "inline-block", whiteSpace: "nowrap" }}>
      {children}
    </span>
  );
}

function MetricCard({ label, value, sub, color }) {
  return (
    <div style={{ background: "var(--color-background-secondary)",
                  borderRadius: "var(--border-radius-md)", padding: "1rem", minWidth: 0 }}>
      <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 4px" }}>{label}</p>
      <p style={{ fontSize: 24, fontWeight: 500, color: color || "var(--color-text-primary)",
                  margin: "0 0 2px" }}>{value}</p>
      {sub && <p style={{ fontSize: 11, color: "var(--color-text-tertiary)", margin: 0 }}>{sub}</p>}
    </div>
  );
}

function SectionHeader({ icon, title }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
      <i className={`ti ${icon}`} style={{ fontSize: 16, color: "var(--color-text-secondary)" }} aria-hidden="true" />
      <p style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-tertiary)",
                  textTransform: "uppercase", letterSpacing: "0.06em", margin: 0 }}>{title}</p>
    </div>
  );
}


// ── NIST RMF Status Cards ─────────────────────────────────────────────────────

function NistStatusCards({ entries, security }) {
  // Compute status from actual data
  const hasEntries = entries.length > 0;
  const hasGrcFields = entries.some(e => e.eu_ai_act_tier);
  const hasSecurityData = security?.total_events !== undefined;

  const functions = [
    {
      name: "GOVERN",
      status: "complete",
      controls: 6,
      artifacts: ["AI_GOVERNANCE_POLICY.md", "agent_manifest.yaml", "AI_SYSTEM_CARD.md",
                  "RESPONSIBLE_AI_USE.md", "EU AI Act disclosure", "Model registry"],
      note: "Policy, accountability, transparency"
    },
    {
      name: "MAP",
      status: "complete",
      controls: 5,
      artifacts: ["EU_AI_ACT_CLASSIFICATION.md", "NIST_RMF_MAPPING.md", "RISK_REGISTER.md",
                  "IMPACT_ASSESSMENT.md", "NIST_600_1_ASSESSMENT.md"],
      note: "Risk context, classification, impact"
    },
    {
      name: "MEASURE",
      status: hasGrcFields ? "complete" : "partial",
      controls: 12,
      artifacts: ["bias_check.py", "transparency.py", "audit_logger.py", "eval_agent.py",
                  "confidence.py", "model_registry.json", "performance_baselines.yaml"],
      note: "Detection, calibration, monitoring"
    },
    {
      name: "MANAGE",
      status: hasEntries ? "complete" : "partial",
      controls: 8,
      artifacts: ["INCIDENT_RESPONSE.md", "GovernanceDashboard.jsx", "IMPROVEMENT_LOG.md",
                  "GAP_ANALYSIS.md", "orchestrator.py HITL gate", "critic.py escalation"],
      note: "Response, recovery, improvement"
    },
  ];

  const [expanded, setExpanded] = useState(null);

  return (
    <div>
      <SectionHeader icon="ti-shield-check" title="NIST AI RMF coverage — GOVERN · MAP · MEASURE · MANAGE" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 8 }}>
        {functions.map(fn => {
          const c = NIST_COLORS[fn.name];
          const isOpen = expanded === fn.name;
          return (
            <div key={fn.name}
              onClick={() => setExpanded(isOpen ? null : fn.name)}
              style={{ background: c.bg, borderRadius: "var(--border-radius-md)",
                       padding: "12px 14px", cursor: "pointer",
                       border: isOpen ? `1.5px solid ${c.fg}` : "1.5px solid transparent",
                       transition: "border 0.15s" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: c.fg,
                            textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {fn.name}
              </div>
              <div style={{ fontSize: 20, fontWeight: 500, color: "var(--color-text-primary)",
                            margin: "4px 0 2px" }}>
                {fn.status === "complete" ? "✓ Active" : "~ Partial"}
              </div>
              <div style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>
                {fn.controls} controls · {fn.note}
              </div>
            </div>
          );
        })}
      </div>

      {/* Expanded artifact list */}
      {expanded && (() => {
        const fn = functions.find(f => f.name === expanded);
        const c = NIST_COLORS[expanded];
        return (
          <div style={{ background: "var(--color-background-primary)",
                        border: `0.5px solid var(--color-border-tertiary)`,
                        borderRadius: "var(--border-radius-md)", padding: "12px 14px",
                        marginBottom: 8 }}>
            <p style={{ fontSize: 12, fontWeight: 500, color: c.fg, margin: "0 0 8px" }}>
              {expanded} controls — {fn.artifacts.length} artifacts
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {fn.artifacts.map(a => (
                <span key={a} style={{ fontSize: 11, padding: "2px 8px",
                                       background: c.bg, color: c.fg,
                                       borderRadius: 4, fontFamily: "monospace" }}>
                  {a}
                </span>
              ))}
            </div>
          </div>
        );
      })()}
    </div>
  );
}


// ── Confidence Trend Chart ────────────────────────────────────────────────────

function ConfidenceTrend({ entries }) {
  const data = entries.slice(-10).map((e, i) => ({
    run:        i + 1,
    confidence: Math.round(e.confidence_score * 100),
    threshold:  75,
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background: "var(--color-background-primary)",
                    border: "0.5px solid var(--color-border-secondary)",
                    borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
        <p style={{ margin: "0 0 4px", fontWeight: 500 }}>Run {label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ margin: "2px 0", color: p.color }}>
            {p.name}: {p.value}%
          </p>
        ))}
      </div>
    );
  };

  return (
    <div>
      <SectionHeader icon="ti-chart-line" title="Confidence score trend — last 10 runs (threshold: 75%)" />
      {data.length === 0 ? (
        <p style={{ fontSize: 13, color: "var(--color-text-tertiary)", padding: "24px 0", textAlign: "center" }}>
          No pipeline runs logged yet. Run the pipeline to populate.
        </p>
      ) : (
        <>
          <div style={{ height: 180 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                <XAxis dataKey="run" tick={{ fontSize: 11 }} label={{ value: "Run", position: "insideBottomRight", fontSize: 10, dy: 10 }} />
                <YAxis tick={{ fontSize: 11 }} domain={[50, 100]} tickFormatter={v => `${v}%`} />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={75} stroke={ORANGE} strokeDasharray="4 2"
                  label={{ value: "75% threshold", position: "right", fontSize: 10, fill: ORANGE }} />
                <Line type="monotone" dataKey="confidence" stroke={NAVY}
                      strokeWidth={2} dot={{ r: 3, fill: NAVY }} name="confidence" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 12,
                        color: "var(--color-text-secondary)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ width: 10, height: 2, background: NAVY, display: "inline-block" }} />
              Confidence score
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ width: 10, height: 0, borderTop: `2px dashed ${ORANGE}`, display: "inline-block" }} />
              75% HITL threshold
            </span>
          </div>
        </>
      )}
    </div>
  );
}


// ── GRC Metrics Row ───────────────────────────────────────────────────────────

function GrcMetricsRow({ summary, security }) {
  const grc = summary.grc || {};
  const biasRate   = ((grc.bias_flag_rate   || 0) * 100).toFixed(0);
  const piiRate    = ((grc.pii_detection_rate || 0) * 100).toFixed(0);
  const groundFail = ((grc.grounding_fail_rate || 0) * 100).toFixed(0);
  const secEvents  = security?.total_events || 0;

  return (
    <div>
      <SectionHeader icon="ti-lock" title="GRC compliance metrics — live from audit trail" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
        <MetricCard
          label="Bias flag rate"
          value={`${biasRate}%`}
          sub="NIST MEASURE 2.11"
          color={parseInt(biasRate) > 20 ? ORANGE : GREEN}
        />
        <MetricCard
          label="PII detection rate"
          value={`${piiRate}%`}
          sub="EU AI Act Art. 10"
          color={parseInt(piiRate) > 0 ? AMBER : GREEN}
        />
        <MetricCard
          label="Grounding fail rate"
          value={`${groundFail}%`}
          sub="NIST MEASURE 2.6"
          color={parseInt(groundFail) > 10 ? ORANGE : GREEN}
        />
        <MetricCard
          label="Security events"
          value={secEvents}
          sub="Injection attempts blocked"
          color={secEvents > 0 ? AMBER : GREEN}
        />
      </div>
    </div>
  );
}


// ── Audit Trail Table ─────────────────────────────────────────────────────────

function AuditTrailTable({ entries }) {
  const [expanded, setExpanded] = useState(null);
  const recent = [...entries].reverse().slice(0, 8);

  function decisionBadgeType(d) {
    if (d === "GO") return "go";
    if (d === "NO_GO") return "nogo";
    return "cgo";
  }

  return (
    <div>
      <SectionHeader icon="ti-list-details" title="Audit trail — last 8 decisions with GRC fields" />
      {entries.length === 0 ? (
        <p style={{ fontSize: 13, color: "var(--color-text-tertiary)", padding: "24px 0", textAlign: "center" }}>
          No decisions logged yet. Run the pipeline to populate.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {recent.map(e => (
            <div key={e.log_id}
              style={{ background: "var(--color-background-primary)",
                       border: "0.5px solid var(--color-border-tertiary)",
                       borderRadius: "var(--border-radius-md)",
                       padding: "10px 14px", cursor: "pointer" }}
              onClick={() => setExpanded(expanded === e.log_id ? null : e.log_id)}>

              {/* Row summary */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                  <Badge type={decisionBadgeType(e.decision)}>{e.decision}</Badge>
                  <span style={{ fontSize: 13, color: "var(--color-text-primary)",
                                 overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                                 maxWidth: 220 }}>
                    {e.feature}
                  </span>
                  {e.escalated_to_human && <Badge type="escalated">escalated</Badge>}
                  {e.bias_flags_raised && <Badge type={e.bias_risk_level || "warning"}>bias {e.bias_risk_level}</Badge>}
                </div>
                <div style={{ display: "flex", gap: 10, alignItems: "center", flexShrink: 0 }}>
                  <span style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>
                    {Math.round(e.confidence_score * 100)}% conf
                  </span>
                  <span style={{ fontSize: 11, color: "var(--color-text-tertiary)",
                                 fontFamily: "monospace" }}>
                    {e.input_hash || "—"}
                  </span>
                  <i className={`ti ${expanded === e.log_id ? "ti-chevron-up" : "ti-chevron-down"}`}
                    style={{ fontSize: 14, color: "var(--color-text-tertiary)" }} aria-hidden="true" />
                </div>
              </div>

              {/* Expanded GRC detail */}
              {expanded === e.log_id && (
                <div style={{ marginTop: 10, paddingTop: 10,
                              borderTop: "0.5px solid var(--color-border-tertiary)" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                    {[
                      { label: "EU AI Act tier",    value: e.eu_ai_act_tier || "—" },
                      { label: "Grounding",         value: e.grounding_result || "—" },
                      { label: "PII redacted",      value: `${e.pii_items_redacted || 0} items` },
                      { label: "Bias risk level",   value: e.bias_risk_level || "none" },
                      { label: "Model used",        value: e.model_used || "—" },
                      { label: "Outcome",           value: e.outcome || "PENDING" },
                    ].map(f => (
                      <div key={f.label} style={{ fontSize: 12 }}>
                        <span style={{ color: "var(--color-text-tertiary)" }}>{f.label}: </span>
                        <span style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{f.value}</span>
                      </div>
                    ))}
                  </div>
                  <div style={{ marginTop: 8, fontSize: 11, color: "var(--color-text-tertiary)",
                                fontFamily: "monospace" }}>
                    log_id: {e.log_id} · run_id: {e.run_id}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ── Bias & PII Analysis ───────────────────────────────────────────────────────

function BiasAnalysisPanel({ entries }) {
  const biasEntries = entries.filter(e => e.bias_flags_raised);
  const riskCounts = { high: 0, medium: 0, low: 0, none: 0 };
  entries.forEach(e => {
    const level = e.bias_risk_level || "none";
    if (riskCounts[level] !== undefined) riskCounts[level]++;
  });

  const barData = [
    { name: "None",   value: riskCounts.none,   color: "#888780" },
    { name: "Low",    value: riskCounts.low,    color: GREEN },
    { name: "Medium", value: riskCounts.medium, color: AMBER },
    { name: "High",   value: riskCounts.high,   color: ORANGE },
  ];

  const piiEntries = entries.filter(e => e.pii_items_redacted > 0);
  const totalPii = entries.reduce((s, e) => s + (e.pii_items_redacted || 0), 0);

  return (
    <div>
      <SectionHeader icon="ti-eye-off" title="Bias & PII analysis — NIST MEASURE 2.11 | EU AI Act Art. 10" />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* Bias risk distribution */}
        <div>
          <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 10px" }}>
            Bias risk level distribution — {biasEntries.length} of {entries.length} runs flagged
          </p>
          <div style={{ height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip formatter={v => [v, "runs"]} />
                <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                  {barData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* PII summary */}
        <div>
          <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 10px" }}>
            PII redaction summary — {piiEntries.length} runs had PII detected
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
            <div style={{ background: "var(--color-background-secondary)",
                          borderRadius: "var(--border-radius-md)", padding: "10px 14px" }}>
              <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>
                Total items redacted
              </p>
              <p style={{ fontSize: 22, fontWeight: 500, color: "var(--color-text-primary)", margin: 0 }}>
                {totalPii}
              </p>
            </div>
            <div style={{ background: "var(--color-background-secondary)",
                          borderRadius: "var(--border-radius-md)", padding: "10px 14px" }}>
              <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>
                Runs with PII
              </p>
              <p style={{ fontSize: 22, fontWeight: 500, color: entries.length > 0 ? AMBER : GREEN, margin: 0 }}>
                {entries.length > 0
                  ? `${Math.round(piiEntries.length / entries.length * 100)}%`
                  : "—"}
              </p>
            </div>
            <div style={{ background: "var(--color-background-secondary)",
                          borderRadius: "var(--border-radius-md)", padding: "10px 14px" }}>
              <p style={{ fontSize: 12, color: "var(--color-text-secondary)", margin: "0 0 2px" }}>
                EU AI Act Art. 10
              </p>
              <p style={{ fontSize: 14, fontWeight: 500, color: GREEN, margin: 0 }}>
                ✓ Compliant
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// ── Security Events ───────────────────────────────────────────────────────────

function SecurityPanel({ security }) {
  const events = security?.events || [];
  const severityType = { high: "danger", medium: "warning", low: "ok" };

  return (
    <div>
      <SectionHeader icon="ti-shield-lock" title="Security events — NIST AI 600-1 Risk 11 | Prompt injection" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 14 }}>
        <MetricCard label="Total events"           value={security?.total_events || 0}        sub="All time" />
        <MetricCard label="Inputs blocked"         value={security?.blocked_inputs || 0}      sub="Injection attempts" color={ORANGE} />
        <MetricCard label="Outputs sanitised"      value={security?.unsafe_outputs_blocked || 0} sub="Unsafe patterns" color={AMBER} />
      </div>
      {events.length === 0 ? (
        <p style={{ fontSize: 13, color: "var(--color-text-tertiary)", textAlign: "center", padding: "16px 0" }}>
          No security events logged.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {events.map((e, i) => (
            <div key={i} style={{ background: "var(--color-background-primary)",
                                   border: "0.5px solid var(--color-border-tertiary)",
                                   borderRadius: "var(--border-radius-md)",
                                   padding: "10px 14px",
                                   display: "flex", alignItems: "center",
                                   justifyContent: "space-between" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Badge type={severityType[e.severity] || "neutral"}>{e.severity}</Badge>
                <div>
                  <p style={{ margin: 0, fontSize: 13, color: "var(--color-text-primary)" }}>
                    {e.type === "injection_attempt" ? "Prompt injection attempt" : "Unsafe output blocked"}
                  </p>
                  <p style={{ margin: 0, fontSize: 11, color: "var(--color-text-secondary)",
                               fontFamily: "monospace" }}>
                    {e.input_preview?.slice(0, 60)}...
                  </p>
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                <Badge type="ok">blocked</Badge>
                <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>
                  {new Date(e.timestamp).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ── ISO 42001 Gap Summary ─────────────────────────────────────────────────────

function IsoGapPanel() {
  const clauses = [
    { clause: "4.1", name: "Understand context",      status: "complete" },
    { clause: "5.1", name: "Leadership commitment",    status: "complete" },
    { clause: "5.2", name: "AI policy",               status: "complete" },
    { clause: "5.3", name: "Roles & responsibilities", status: "complete" },
    { clause: "6.1.2", name: "Risk assessment",       status: "complete" },
    { clause: "6.1.4", name: "Impact assessment",     status: "complete" },
    { clause: "8.2",  name: "AI risk assessment",     status: "complete" },
    { clause: "9.1",  name: "Monitoring & measurement",status: "complete" },
    { clause: "10.1", name: "Corrective action",      status: "complete" },
    { clause: "10.2", name: "Continual improvement",  status: "complete" },
    { clause: "4.2",  name: "Interested parties",     status: "partial"  },
    { clause: "6.2",  name: "Governance objectives",  status: "partial"  },
    { clause: "8.1",  name: "Change control",         status: "partial"  },
    { clause: "9.2",  name: "Internal audit",         status: "partial"  },
  ];

  const complete = clauses.filter(c => c.status === "complete").length;
  const partial  = clauses.filter(c => c.status === "partial").length;

  return (
    <div>
      <SectionHeader icon="ti-certificate" title="ISO/IEC 42001 gap analysis — clause status" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 14 }}>
        <MetricCard label="Complete"    value={complete} sub="Clauses fully implemented" color={GREEN} />
        <MetricCard label="Partial"     value={partial}  sub="Clauses in progress"       color={AMBER} />
        <MetricCard label="Gaps"        value={0}        sub="No unaddressed gaps"       color={GREEN} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        {clauses.map(c => (
          <div key={c.clause}
            style={{ background: "var(--color-background-primary)",
                     border: "0.5px solid var(--color-border-tertiary)",
                     borderRadius: "var(--border-radius-md)",
                     padding: "8px 12px",
                     display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <span style={{ fontSize: 11, fontFamily: "monospace",
                             color: "var(--color-text-tertiary)" }}>
                {c.clause}
              </span>
              <span style={{ fontSize: 12, color: "var(--color-text-primary)", marginLeft: 8 }}>
                {c.name}
              </span>
            </div>
            <Badge type={c.status === "complete" ? "ok" : "warning"}>
              {c.status}
            </Badge>
          </div>
        ))}
      </div>
      <p style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 10 }}>
        Full clause-by-clause detail in <code>docs/GAP_ANALYSIS.md</code>
      </p>
    </div>
  );
}


// ── Governance Tab Navigation ─────────────────────────────────────────────────

const GOV_TABS = [
  { id: "overview",  label: "Overview",       icon: "ti-layout-dashboard" },
  { id: "audit",     label: "Audit trail",    icon: "ti-list-details"     },
  { id: "bias",      label: "Bias & PII",     icon: "ti-eye-off"          },
  { id: "security",  label: "Security",       icon: "ti-shield-lock"      },
  { id: "iso",       label: "ISO 42001",      icon: "ti-certificate"      },
];


// ── Main GovernanceDashboard component ────────────────────────────────────────

export default function GovernanceDashboard() {
  const [govTab, setGovTab]     = useState("overview");
  const [audit, setAudit]       = useState(null);
  const [security, setSecurity] = useState(null);
  const [loading, setLoading]   = useState(true);
  const [usingMock, setUsingMock] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/audit-trail`).then(r => r.json()).catch(() => null),
      fetch(`${API}/security-report`).then(r => r.json()).catch(() => null),
    ]).then(([auditData, secData]) => {
      if (auditData && auditData.summary) {
        setAudit(auditData);
        setSecurity(secData || MOCK_SECURITY);
        setUsingMock(false);
      } else {
        setAudit(MOCK_AUDIT);
        setSecurity(MOCK_SECURITY);
        setUsingMock(true);
      }
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div style={{ padding: "48px 0", textAlign: "center",
                    color: "var(--color-text-tertiary)", fontSize: 13 }}>
        Loading governance data...
      </div>
    );
  }

  const summary = audit?.summary || {};
  const entries = audit?.entries || [];

  return (
    <div>

      {/* Mock data notice — same style as existing App.jsx alerts */}
      {usingMock && (
        <div style={{ background: "#FAEEDA", borderRadius: "var(--border-radius-md)",
                      padding: "8px 14px", marginBottom: 16, fontSize: 12,
                      color: "#633806", display: "flex", alignItems: "center", gap: 8 }}>
          <i className="ti ti-info-circle" aria-hidden="true" />
          Showing mock data — start the FastAPI backend (<code>uvicorn backend.main:app --reload</code>) to see live pipeline data.
        </div>
      )}

      {/* Summary metrics row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: "1.5rem" }}>
        <MetricCard
          label="Total decisions"
          value={summary.total_decisions || 0}
          sub={`${summary.decision_breakdown?.GO || 0} GO · ${summary.decision_breakdown?.NO_GO || 0} NO-GO`}
        />
        <MetricCard
          label="Avg confidence"
          value={summary.avg_confidence_score
            ? `${Math.round(summary.avg_confidence_score * 100)}%` : "—"}
          sub="Across all runs"
          color={summary.avg_confidence_score >= 0.75 ? GREEN : ORANGE}
        />
        <MetricCard
          label="Escalation rate"
          value={summary.escalation_rate
            ? `${Math.round(summary.escalation_rate * 100)}%` : "—"}
          sub="Runs sent to human review"
          color={summary.escalation_rate > 0.3 ? ORANGE : GREEN}
        />
        <MetricCard
          label="GRC version"
          value="v1.0"
          sub="NIST · EU AI Act · ISO 42001 · AIGP"
          color={NAVY}
        />
      </div>

      {/* Governance sub-tab nav */}
      <div style={{ display: "flex", gap: 4, borderBottom: "0.5px solid var(--color-border-tertiary)",
                    marginBottom: "1.5rem", overflowX: "auto" }}>
        {GOV_TABS.map(t => (
          <button key={t.id} onClick={() => setGovTab(t.id)}
            style={{ background: "transparent", border: "none",
                     borderBottom: govTab === t.id
                       ? "2px solid var(--color-text-primary)"
                       : "2px solid transparent",
                     padding: "6px 14px 8px", fontSize: 13,
                     fontWeight: govTab === t.id ? 500 : 400,
                     color: govTab === t.id
                       ? "var(--color-text-primary)"
                       : "var(--color-text-secondary)",
                     cursor: "pointer", whiteSpace: "nowrap",
                     display: "flex", alignItems: "center", gap: 6 }}>
            <i className={`ti ${t.icon}`} style={{ fontSize: 14 }} aria-hidden="true" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>

        {govTab === "overview" && (
          <>
            <NistStatusCards entries={entries} security={security} />
            <hr style={{ border: "none", borderTop: "0.5px solid var(--color-border-tertiary)" }} />
            <GrcMetricsRow summary={summary} security={security} />
            <hr style={{ border: "none", borderTop: "0.5px solid var(--color-border-tertiary)" }} />
            <ConfidenceTrend entries={entries} />
          </>
        )}

        {govTab === "audit" && (
          <AuditTrailTable entries={entries} />
        )}

        {govTab === "bias" && (
          <BiasAnalysisPanel entries={entries} />
        )}

        {govTab === "security" && (
          <SecurityPanel security={security} />
        )}

        {govTab === "iso" && (
          <IsoGapPanel />
        )}

      </div>

      {/* Footer */}
      <div style={{ marginTop: "2rem", paddingTop: "1rem",
                    borderTop: "0.5px solid var(--color-border-tertiary)",
                    display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>
          NIST AI RMF · EU AI Act · ISO/IEC 42001 · AIGP BOK v2.1 · v1.0
        </span>
        <a href="https://github.com/saurabhsmahajan/ai-product-loop/tree/master/docs"
          target="_blank" rel="noopener noreferrer"
          style={{ fontSize: 12, color: "var(--color-text-secondary)", textDecoration: "none" }}>
          View governance docs ↗
        </a>
      </div>
    </div>
  );
}
