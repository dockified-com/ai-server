"""Reasoning message builders. These reproduce the EXACT user-message formats
from the original backend (backend/app/features/tutor/prompts.py) so streamed
output is byte-for-byte equivalent to pre-extraction behavior.

Context is split: server_context carries secret/server-derived data sealed in
the session token (problem prompt, rubric, RAG chunks); client_context carries
the browser-supplied turn data (student code, response text, question)."""

from __future__ import annotations


def _socratic(server: dict, client: dict) -> str:
    attempt_count = client.get("attempt_count", 1)
    tier = (
        "high-level conceptual" if attempt_count <= 2
        else "specific line/concept" if attempt_count <= 4
        else "analogous simpler example"
    )
    problem_prompt = server.get("problem_prompt", "")
    student_code = client.get("student_code", "")
    stdout = client.get("stdout")
    stderr = client.get("stderr")
    return (
        f"Problem:\n{problem_prompt}\n\n"
        f"Student code (attempt {attempt_count}):\n```\n{student_code}\n```\n\n"
        f"Output:\nstdout: {stdout or '(none)'}\nstderr: {stderr or '(none)'}\n\n"
        f"Guidance tier: {tier}. Provide a Socratic hint only."
    )


def _understanding(server: dict, client: dict) -> str:
    rubric = server.get("rubric", "")
    student_response = client.get("response", "")
    attempt_count = client.get("attempt_number", 1)
    return (
        f"Evaluation rubric:\n{rubric}\n\n"
        f"Student response (attempt {attempt_count}):\n{student_response}\n\n"
        "Evaluate the response."
    )


def _ask(server: dict, client: dict) -> str:
    chunks = server.get("chunks", [])
    block_context = server.get("block_context")
    question = client.get("question", "")
    context = "\n\n".join(f"[Chunk {i + 1}]\n{c}" for i, c in enumerate(chunks))
    block_section = f"\n\nCurrent block context:\n{block_context}" if block_context else ""
    return f"Course context:\n{context}{block_section}\n\nStudent question: {question}"


_BUILDERS = {
    "socratic": _socratic,
    "understanding-check": _understanding,
    "ask": _ask,
}


def build_user_message(agent: str, server_context: dict, client_context: dict) -> str:
    return _BUILDERS[agent](server_context, client_context)
