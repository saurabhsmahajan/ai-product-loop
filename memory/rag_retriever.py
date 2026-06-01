# memory/rag_retriever.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from memory.chroma_store import retrieve_similar


def retrieve_context(query: str, n_results: int = 3, source: str = "both", mode: str = None) -> str:
    """
    Retrieves relevant past context from ChromaDB.
    mode: "decisions" | "interviews" | "both"
    Returns a formatted string ready to inject into any agent prompt.
    """

    context_parts = []

    # support both old "mode" and new "source" parameter
    _filter = source if source != "both" or mode is None else mode
    if _filter in ("decisions", "both"):
        decision_results = retrieve_similar(query, "decisions", n_results)
        if decision_results:
            context_parts.append("RELEVANT PAST DECISIONS:")
            for r in decision_results:
                context_parts.append(
                    f"- (similarity distance: {r['distance']:.3f})\n  {r['text'][:300]}"
                )

    if _filter in ("interviews", "both"):
        interview_results = retrieve_similar(query, "interviews", n_results)
        if interview_results:
            context_parts.append("\nRELEVANT PAST INTERVIEW INSIGHTS:")
            for r in interview_results:
                context_parts.append(
                    f"- (similarity distance: {r['distance']:.3f})\n  {r['text'][:300]}"
                )

    if not context_parts:
        return "No relevant past context found."

    return "\n".join(context_parts)


def retrieve_for_orchestrator(feature: str) -> str:
    """Retrieves context specifically for the Orchestrator Agent."""
    return retrieve_context(
        query=f"pipeline decision for: {feature}",
        mode="decisions",
        n_results=3
    )


def retrieve_for_synthesis(feature: str) -> str:
    """Retrieves context specifically for the Synthesis Agent."""
    return retrieve_context(
        query=f"user pain themes for: {feature}",
        mode="interviews",
        n_results=3
    )


def retrieve_for_decider(feature: str, signals: list) -> str:
    """Retrieves context specifically for the Decider Agent."""
    signal_text = " | ".join(signals) if signals else feature
    return retrieve_context(
        query=f"go no-go decision with signals: {signal_text}",
        mode="both",
        n_results=2
    )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RAG RETRIEVER — Stage 04: Learn")
    print("=" * 60)

    feature = "An AI assistant that automatically summarises customer support tickets."

    print("\n[Orchestrator context]")
    print(retrieve_for_orchestrator(feature))

    print("\n[Synthesis context]")
    print(retrieve_for_synthesis(feature))

    print("\n[Decider context]")
    print(retrieve_for_decider(feature, ["hallucination rate high", "governance flagged"]))