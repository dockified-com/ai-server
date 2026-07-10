"""ENTRY — merge mint/JWT server_context into TutorState (Next wins for M1/M3)."""

from __future__ import annotations

from typing import Any

from app.graphs.tutor_session.state import TutorState


def entry_node(state: TutorState) -> dict[str, Any]:
    """Load mint context and overlay profile (M1) + task (M3).

    Conflict rule: mint/Next snapshot wins over checkpoint for M1 and unlock/task fields.
    Dialogue messages (M2) are preserved from state/checkpoint and extended with turn input.
    """
    mint = dict(state.get("mint") or {})
    sc = dict(mint.get("server_context") or {})

    # --- M1 profile (checkpoint base, then mint overlay wins) ---
    profile = dict(state.get("profile") or {})
    sc_profile = sc.get("profile") if isinstance(sc.get("profile"), dict) else {}
    if sc_profile:
        profile.update(sc_profile)

    def _set_profile(snake: str, camel: str, *sources: dict) -> None:
        for src in sources:
            if not src:
                continue
            if camel in src and src[camel] is not None:
                profile[snake] = src[camel]
                profile[camel] = src[camel]
                return
            if snake in src and src[snake] is not None:
                profile[snake] = src[snake]
                profile[camel] = src[snake]
                return

    # Mint wins: check sc_profile then sc root (always overwrite when mint provides value)
    _set_profile("preferred_name", "preferredName", sc_profile, sc)
    _set_profile("assessed_level", "assessedLevel", sc_profile, sc)
    _set_profile("locale", "locale", sc_profile, sc)

    # Normalize any remaining camel-only keys left from checkpoint/sc merge
    if "preferredName" in profile and profile.get("preferred_name") is None:
        profile["preferred_name"] = profile["preferredName"]
    if "assessedLevel" in profile and profile.get("assessed_level") is None:
        profile["assessed_level"] = profile["assessedLevel"]
    if "preferred_name" in profile:
        profile["preferredName"] = profile["preferred_name"]
    if "assessed_level" in profile:
        profile["assessedLevel"] = profile["assessed_level"]

    # --- M3 task (checkpoint base, mint overlay wins) ---
    task = dict(state.get("task") or {})
    sc_task = sc.get("task") if isinstance(sc.get("task"), dict) else {}
    if sc_task:
        task.update(sc_task)

    stage = (
        sc_task.get("tutor_stage")
        or sc_task.get("tutorStage")
        or sc.get("tutorStage")
        or sc.get("tutor_stage")
        or task.get("tutor_stage")
        or task.get("tutorStage")
    )
    if stage:
        task["tutor_stage"] = stage
        task["tutorStage"] = stage

    for camel, snake in (
        ("enrollmentId", "enrollment_id"),
        ("courseId", "course_id"),
        ("currentLessonId", "current_lesson_id"),
        ("currentBlockId", "current_block_id"),
        ("lastVerdict", "last_verdict"),
        ("askRemaining", "ask_remaining"),
    ):
        val = None
        for src in (sc_task, sc, task):
            if camel in src and src[camel] is not None:
                val = src[camel]
                break
            if snake in src and src[snake] is not None:
                val = src[snake]
                break
        if val is not None:
            task[snake] = val
            task[camel] = val

    # enrollment from sub claim if missing
    if not task.get("enrollment_id"):
        sub = str(mint.get("sub") or "")
        if sub.startswith("enrollment:"):
            task["enrollment_id"] = sub.removeprefix("enrollment:")
            task["enrollmentId"] = task["enrollment_id"]
        elif sc.get("enrollmentId") or sc.get("enrollment_id"):
            task["enrollment_id"] = sc.get("enrollmentId") or sc.get("enrollment_id")
            task["enrollmentId"] = task["enrollment_id"]

    # course_title: mint wins when present
    course_title = (
        sc.get("courseTitle")
        or sc.get("course_title")
        or state.get("course_title")
        or ""
    )

    messages = list(state.get("messages") or [])

    return {
        "mint": mint,
        "profile": profile,
        "task": task,
        "course_title": course_title,
        "messages": messages,
        "tool_results": list(state.get("tool_results") or []),
        "assistant_text": state.get("assistant_text") or "",
    }
