# memory/chroma_store.py

import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from chromadb.config import Settings


# ── ChromaDB client — persists to disk locally ─────────────────────────────
def get_chroma_client():
    """Returns a persistent ChromaDB client stored in the chroma_db/ folder."""
    return chromadb.PersistentClient(path="chroma_db")


def get_or_create_collection(name: str):
    """Gets an existing collection or creates it if it doesn't exist."""
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)


# ── Write interview transcripts ────────────────────────────────────────────
def store_interview_transcripts(data_folder: str = "data") -> int:
    """
    Reads all interview transcripts from data/ and stores them in ChromaDB.
    Each question-answer pair is stored as a separate embedding.
    Returns the number of entries stored.
    """
    collection = get_or_create_collection("interviews")
    stored_count = 0

    if not os.path.exists(data_folder):
        print("No data folder found.")
        return 0

    for filename in os.listdir(data_folder):
        if not filename.startswith("INT_") or not filename.endswith(".json"):
            continue

        filepath = os.path.join(data_folder, filename)
        with open(filepath, "r") as f:
            transcript = json.load(f)

        interview_id = transcript.get("interview_id", filename)
        feature = transcript.get("feature_hypothesis", "")

        for q in transcript.get("questions", []):
            # Build a rich text chunk from question + answer + follow-up
            text_chunk = f"""
Feature: {feature}
Question: {q.get('question', '')}
Answer: {q.get('user_answer', '')}
Follow-up: {q.get('follow_up', '')}
Follow-up answer: {q.get('follow_up_answer', '')}
""".strip()

            doc_id = f"{interview_id}_{q.get('question_id', 'Q')}"

            # Store in ChromaDB — it auto-generates embeddings
            collection.upsert(
                documents=[text_chunk],
                ids=[doc_id],
                metadatas=[{
                    "interview_id": interview_id,
                    "feature": feature,
                    "question_id": q.get("question_id", "")
                }]
            )
            stored_count += 1

    print(f"✅ Stored {stored_count} interview Q&A chunks in ChromaDB.")
    return stored_count


# ── Write decisions ────────────────────────────────────────────────────────
def store_decision(
    run_id: str,
    feature: str,
    orchestrator_report: dict,
    decider_report: dict,
    reflexion_report: dict
) -> None:
    """
    Stores a full pipeline decision as an embedding in ChromaDB.
    The text chunk includes the decision, reasoning chain, and key signals.
    """
    collection = get_or_create_collection("decisions")

    decision = decider_report.get("decision", "UNKNOWN")
    confidence = decider_report.get("confidence_score", 0)
    reasoning = " | ".join(decider_report.get("reasoning_chain", []))
    risks = " | ".join(decider_report.get("key_risks", []))
    signals = " | ".join(orchestrator_report.get("signals", []))
    conditions = " | ".join(decider_report.get("conditions_if_conditional", []))

    text_chunk = f"""
Feature: {feature}
Decision: {decision}
Confidence: {confidence}
Signals: {signals}
Reasoning: {reasoning}
Key risks: {risks}
Conditions: {conditions}
Escalated to human: {decider_report.get('escalate_to_human', False)}
""".strip()

    collection.upsert(
        documents=[text_chunk],
        ids=[run_id],
        metadatas=[{
            "feature": feature,
            "decision": decision,
            "confidence_score": str(confidence),
            "escalated": str(decider_report.get("escalate_to_human", False)),
            "agg_confidence": str(orchestrator_report.get("aggregated_confidence_score", 0))
        }]
    )

    print(f"✅ Stored decision '{decision}' for run {run_id} in ChromaDB.")


# ── Query ──────────────────────────────────────────────────────────────────
def retrieve_similar(query: str, collection_name: str, n_results: int = 3) -> list:
    """
    Retrieves the top-n semantically similar entries from a collection.
    Used by agents to get relevant past context before acting.
    """
    collection = get_or_create_collection(collection_name)

    # Check if collection has any entries
    count = collection.count()
    if count == 0:
        print(f"Collection '{collection_name}' is empty.")
        return []

    # Cap n_results to what's available
    n_results = min(n_results, count)

    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    retrieved = []
    for i, doc in enumerate(results["documents"][0]):
        retrieved.append({
            "text": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return retrieved


# ── Load and store today's data ────────────────────────────────────────────
def load_and_store_all() -> None:
    """
    Loads all existing data files and stores them in ChromaDB.
    Safe to run multiple times — upsert prevents duplicates.
    """
    print("\n" + "=" * 60)
    print("CHROMADB VECTOR STORE — Stage 04: Learn")
    print("=" * 60)

    # Store interview transcripts
    print("\nStoring interview transcripts...")
    store_interview_transcripts("data")

    # Store pipeline decision if all reports exist
    orch_path = "data/orchestrator_report.json"
    dec_path = "data/decider_report.json"
    ref_path = "data/reflexion_report.json"

    if all(os.path.exists(p) for p in [orch_path, dec_path, ref_path]):
        print("\nStoring pipeline decision...")
        with open(orch_path) as f:
            orch = json.load(f)
        with open(dec_path) as f:
            dec = json.load(f)
        with open(ref_path) as f:
            ref = json.load(f)

        run_id = orch.get("pipeline_run_id", "RUN_UNKNOWN")
        feature = "An AI assistant that automatically summarises customer support tickets and suggests responses to agents."
        store_decision(run_id, feature, orch, dec, ref)
    else:
        print("⚠️  Some decision files missing — skipping decision storage.")

    # Test retrieval
    print("\nTesting retrieval from ChromaDB...")
    print("\nQuery: 'high hallucination rate and governance issues'")
    results = retrieve_similar(
        "high hallucination rate and governance issues",
        "decisions",
        n_results=1
    )
    for r in results:
        print(f"  Match (distance {r['distance']:.3f}): {r['text'][:200]}...")

    print("\nQuery: 'ticket volume and support team pain'")
    results = retrieve_similar(
        "ticket volume and support team pain",
        "interviews",
        n_results=2
    )
    for r in results:
        print(f"  Match (distance {r['distance']:.3f}): {r['text'][:150]}...")


if __name__ == "__main__":
    load_and_store_all()