# backend/routes.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Day 12 — security layer
try:
    from agents.security_layer import sanitise_input, validate_output, get_security_report
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False


# ── Request models ─────────────────────────────────────────────────────────

class FeatureRequest(BaseModel):
    feature_hypothesis: str
    run_id: str = None


class OutcomeUpdate(BaseModel):
    log_id: str
    outcome: str
    notes: str = ""


# ── Helper ─────────────────────────────────────────────────────────────────

def load_json(path: str) -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


# ── Stage 01: Discover ─────────────────────────────────────────────────────

@router.post("/discover")
async def discover(request: FeatureRequest):
    """Runs synthesis on existing transcripts and returns opportunity map."""
    try:
        from agents.synthesis_agent import run_synthesis
        result = run_synthesis()
        return {"status": "success", "stage": "discover", "result": result}
    except Exception as e:
        return {"status": "error", "stage": "discover", "error": str(e)}


# ── Stage 02: Evaluate ─────────────────────────────────────────────────────

@router.post("/evaluate")
async def evaluate(request: FeatureRequest):
    """Runs persona simulation, hallucination eval, and governance check."""
    try:
        from agents.persona_agent import simulate_personas
        from agents.eval_agent import run_hallucination_eval
        from agents.governance import run_governance_check

        persona_result = simulate_personas(request.feature_hypothesis)
        os.makedirs("data", exist_ok=True)
        with open("data/persona_simulation.json", "w") as f:
            json.dump(persona_result, f, indent=2)

        eval_result = load_json("data/hallucination_eval_report.json")
        gov_result  = load_json("data/governance_report.json")

        return {
            "status":     "success",
            "stage":      "evaluate",
            "persona":    persona_result,
            "eval":       eval_result,
            "governance": gov_result
        }
    except Exception as e:
        return {"status": "error", "stage": "evaluate", "error": str(e)}


# ── Stage 03: Decide ───────────────────────────────────────────────────────

@router.post("/decide")
async def decide(request: FeatureRequest):
    """Runs Orchestrator + Decider + Reflexion Loop."""
    try:
        from agents.orchestrator import run_orchestrator
        from agents.decider import run_decider
        from agents.critic import run_reflexion_loop

        orch_result = run_orchestrator(request.feature_hypothesis)
        dec_result  = run_decider(orch_result, request.feature_hypothesis)
        ref_result  = run_reflexion_loop(
            dec_result,
            request.feature_hypothesis,
            orch_result
        )

        return {
            "status":      "success",
            "stage":       "decide",
            "orchestrator": orch_result,
            "decider":      dec_result,
            "reflexion":    ref_result
        }
    except Exception as e:
        return {"status": "error", "stage": "decide", "error": str(e)}


# ── Stage 04: Learn ────────────────────────────────────────────────────────

@router.post("/learn")
async def learn(request: FeatureRequest):
    """Stores decision in ChromaDB and logs to audit trail."""
    try:
        from memory.chroma_store import store_decision
        from memory.audit_logger import log_decision

        run_id = request.run_id or f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        orch = load_json("data/orchestrator_report.json")
        dec  = load_json("data/decider_report.json")
        ref  = load_json("data/reflexion_report.json")

        final_decision = ref.get("final_decision", dec)

        store_decision(run_id, request.feature_hypothesis, orch, dec, ref)

        entry = log_decision(
            run_id=run_id,
            feature=request.feature_hypothesis,
            stage="Stage 03 — Decide",
            agent_name="Decider + Reflexion Loop",
            input_signals=orch.get("signals", []),
            reasoning_chain=final_decision.get("reasoning_chain", []),
            decision=final_decision.get("decision", "UNKNOWN"),
            confidence_score=final_decision.get("confidence_score", 0),
            escalated_to_human=final_decision.get("escalate_to_human", False),
            model_used="gpt-4o-mini",
            tokens_consumed=0,
            outcome="PENDING"
        )

        return {
            "status":    "success",
            "stage":     "learn",
            "log_entry": entry
        }
    except Exception as e:
        return {"status": "error", "stage": "learn", "error": str(e)}


# ── Full pipeline ──────────────────────────────────────────────────────────

@router.post("/run-pipeline")
async def run_pipeline(request: FeatureRequest):
    """Triggers all 4 stages end-to-end with one API call."""
    try:
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        request.run_id = run_id

        # Day 12 — sanitise input before anything runs
        if SECURITY_AVAILABLE:
            sec_check = sanitise_input(request.feature_hypothesis, "run-pipeline")
            if sec_check["blocked"]:
                return {"status": "blocked", "reason": "Input failed security check", "threats": sec_check["threats"]}
            request.feature_hypothesis = sec_check["sanitised_text"]

        print(f"\n{'='*60}")
        print(f"FULL PIPELINE RUN — {run_id}")
        print(f"Feature: {request.feature_hypothesis}")
        print(f"{'='*60}")

        # Stage 01
        print("\n[Stage 01] Discover...")
        from agents.synthesis_agent import run_synthesis
        discover_result = run_synthesis()

        # Stage 02
        print("\n[Stage 02] Evaluate...")
        from agents.persona_agent import simulate_personas
        from agents.confidence import run_confidence_calibration

        persona_result = simulate_personas(request.feature_hypothesis)
        with open("data/persona_simulation.json", "w") as f:
            json.dump(persona_result, f, indent=2)

        eval_report = load_json("data/hallucination_eval_report.json")
        ai_outputs = [
            {"statement": "Customer login issue", "stated_confidence": 0.9, "actual_outcome": 1},
            {"statement": "Server outage reported", "stated_confidence": 0.85, "actual_outcome": 0},
        ]
        confidence_result = run_confidence_calibration(ai_outputs, eval_report)

        # Stage 03
        print("\n[Stage 03] Decide...")
        from agents.orchestrator import run_orchestrator
        from agents.decider import run_decider
        from agents.critic import run_reflexion_loop

        orch_result = run_orchestrator(request.feature_hypothesis)
        dec_result  = run_decider(orch_result, request.feature_hypothesis)
        ref_result  = run_reflexion_loop(
            dec_result, request.feature_hypothesis, orch_result
        )

        # Stage 04
        print("\n[Stage 04] Learn...")
        from memory.chroma_store import store_decision
        from memory.audit_logger import log_decision

        final_decision = ref_result.get("final_decision", dec_result)
        store_decision(run_id, request.feature_hypothesis, orch_result, dec_result, ref_result)

        log_entry = log_decision(
            run_id=run_id,
            feature=request.feature_hypothesis,
            stage="Stage 03 — Decide",
            agent_name="Decider + Reflexion Loop",
            input_signals=orch_result.get("signals", []),
            reasoning_chain=final_decision.get("reasoning_chain", []),
            decision=final_decision.get("decision", "UNKNOWN"),
            confidence_score=final_decision.get("confidence_score", 0),
            escalated_to_human=final_decision.get("escalate_to_human", False),
            model_used="gpt-4o-mini",
            tokens_consumed=0,
            outcome="PENDING"
        )

        from agents.cost_tracker import get_cost_report
        cost_report = get_cost_report()

        print(f"\n✅ Pipeline complete — {run_id}")

        return {
            "status":     "success",
            "run_id":     run_id,
            "decision":   final_decision.get("decision"),
            "confidence": final_decision.get("confidence_score"),
            "escalated":  final_decision.get("escalate_to_human"),
            "cost":       cost_report.get("total_cost_usd"),
            "stages": {
                "discover":  discover_result,
                "evaluate":  {"persona": persona_result, "confidence": confidence_result},
                "decide":    {"orchestrator": orch_result, "reflexion": ref_result},
                "learn":     log_entry
            }
        }

    except Exception as e:
        return {"status": "error", "stage": "run-pipeline", "error": str(e)}


# ── Utility endpoints ──────────────────────────────────────────────────────

@router.get("/cost-report")
async def cost_report():
    """Returns full cost breakdown by agent and model."""
    from agents.cost_tracker import get_cost_report
    return get_cost_report()


@router.get("/audit-trail")
async def audit_trail():
    """Returns the full audit trail."""
    from memory.audit_logger import load_audit_trail, get_audit_summary
    return {
        "summary": get_audit_summary(),
        "entries": load_audit_trail()
    }


@router.get("/security-report")
async def security_report():
    """Returns the full security event log."""
    if SECURITY_AVAILABLE:
        return get_security_report()
    return {"status": "security layer not available"}


@router.post("/calibrate")
async def calibrate():
    """Runs the Calibration Analysis Agent over the audit trail."""
    try:
        from agents.calibration_agent import analyse_calibration
        result = analyse_calibration()
        return {"status": "success", "report": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/update-outcome")
async def update_outcome(request: OutcomeUpdate):
    """Updates the outcome of a logged decision post-launch."""
    from memory.audit_logger import update_outcome
    success = update_outcome(request.log_id, request.outcome, request.notes)
    return {"status": "success" if success else "not_found", "log_id": request.log_id}