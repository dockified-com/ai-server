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
    question = client.get("question", "") or server.get("question", "")
    context = "\n\n".join(f"[Chunk {i + 1}]\n{c}" for i, c in enumerate(chunks))
    if not context:
        # Inject-only path: lesson summary / objectives / block prompt from Next
        parts = []
        if server.get("lesson_summary"):
            parts.append(f"Lesson summary: {server['lesson_summary']}")
        if server.get("lesson_objectives"):
            parts.append(f"Objectives: {server['lesson_objectives']}")
        if server.get("block_prompt"):
            parts.append(f"Block: {server['block_prompt']}")
        context = "\n".join(parts) if parts else "(no extra chunks)"
    block_section = f"\n\nCurrent block context:\n{block_context}" if block_context else ""
    return f"Course context:\n{context}{block_section}\n\nStudent question: {question}"


def _tutor_open(server: dict, client: dict) -> str:
    course = server.get("courseTitle") or server.get("course_title") or "this course"
    name = server.get("preferredName") or server.get("preferred_name")
    lesson = server.get("lessonTitle") or server.get("lesson_title") or ""
    if name:
        return (
            f"Course: {course}. Lesson: {lesson}. "
            f"Student preferred name already known: {name}. "
            "Greet them by name and invite them to continue when ready. Do not teach yet."
        )
    return (
        f"Course: {course}. Lesson: {lesson}. "
        "Open the session: greet briefly, mention the course, and ask what name they want you to use. "
        "Do not teach concepts yet."
    )


def _pre_assess(server: dict, client: dict) -> str:
    name = server.get("preferredName") or server.get("preferred_name") or "student"
    topics = server.get("topics") or server.get("lesson_objectives") or []
    topics_s = ", ".join(topics) if isinstance(topics, list) else str(topics)
    user_msg = client.get("message") or server.get("user_message") or ""
    prior = server.get("recentTurns") or server.get("recent_turns") or []
    prior_s = ""
    if isinstance(prior, list) and prior:
        prior_s = "\n".join(
            f"- {t.get('role', '?')}: {t.get('text', t.get('assistantText', t.get('userInput', '')))}"
            for t in prior[-6:]
            if isinstance(t, dict)
        )
    return (
        f"Student name: {name}.\n"
        f"Course topics to probe: {topics_s or 'general programming for this course'}.\n"
        f"Prior turns:\n{prior_s or '(none)'}\n\n"
        f"Student message: {user_msg or '(session just started — ask first pre-assessment question)'}\n"
        "Continue the pre-assessment. After enough signal, propose beginner|intermediate|advanced and ask for confirmation."
    )


def _final_clarify(server: dict, client: dict) -> str:
    prompt = server.get("challenge_prompt") or server.get("prompt") or ""
    question = client.get("question") or client.get("message") or server.get("user_message") or ""
    return (
        f"Final evaluation challenge wording:\n{prompt}\n\n"
        f"Student question about wording only:\n{question}\n\n"
        "Clarify wording only. No hints, no code, no strategy."
    )


def _tts(_server: dict, _client: dict) -> str:
    return "TTS session — no text generation required."


_BUILDERS = {
    "socratic": _socratic,
    "understanding-check": _understanding,
    "ask": _ask,
    "tutor_open": _tutor_open,
    "pre_assess": _pre_assess,
    "final_clarify": _final_clarify,
    "tts": _tts,
}


def build_user_message(agent: str, server_context: dict, client_context: dict) -> str:
    builder = _BUILDERS.get(agent)
    if builder is None:
        # Fallback so unknown stream agents still get a usable message
        return str(client_context.get("message") or server_context.get("user_message") or "Continue.")
    return builder(server_context, client_context)
