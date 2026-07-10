"""LLM + tool loop for tutor_session nodes (max tool rounds, Gemini provider)."""

from __future__ import annotations

import json
from typing import Any, Callable, Awaitable

from google.genai import types

from app.providers.gemini_provider import TEXT_MODEL, gemini_client
from app.graphs.tutor_session.tools.profile import SAVE_PROFILE_DECLARATION, save_profile
from app.graphs.tutor_session.tools.progress import CHECK_PROGRESS_DECLARATION, check_progress

MAX_TOOL_ROUNDS = 3
DEFAULT_MAX_TOKENS = 512

ToolHandler = Callable[..., Awaitable[dict[str, Any]]]


def enrollment_id_from_state(state: dict[str, Any]) -> str:
    task = state.get("task") or {}
    mint = state.get("mint") or {}
    sc = mint.get("server_context") or {}
    return str(
        task.get("enrollment_id")
        or task.get("enrollmentId")
        or sc.get("enrollmentId")
        or sc.get("enrollment_id")
        or mint.get("sub", "").removeprefix("enrollment:")
        or ""
    )


async def _dispatch_tool(
    name: str,
    args: dict[str, Any],
    enrollment_id: str,
    allowed: set[str],
) -> dict[str, Any]:
    if name not in allowed:
        return {"ok": False, "error": f"tool not allowed in this node: {name}"}
    if name == "save_profile":
        return await save_profile(
            enrollment_id,
            preferred_name=args.get("preferred_name") or args.get("preferredName"),
            assessed_level=args.get("assessed_level") or args.get("assessedLevel"),
        )
    if name == "check_progress":
        return await check_progress(enrollment_id)
    return {"ok": False, "error": f"unknown tool: {name}"}


def _declarations_for(allowed: set[str]) -> list[types.FunctionDeclaration]:
    out: list[types.FunctionDeclaration] = []
    if "save_profile" in allowed:
        out.append(SAVE_PROFILE_DECLARATION)
    if "check_progress" in allowed:
        out.append(CHECK_PROGRESS_DECLARATION)
    return out


async def run_node_llm(
    *,
    system_prompt: str,
    user_message: str,
    state: dict[str, Any],
    allowed_tools: set[str] | None = None,
    max_tool_rounds: int = MAX_TOOL_ROUNDS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    model: str = TEXT_MODEL,
) -> tuple[str, list[dict[str, Any]]]:
    """Run Gemini with optional tools for up to max_tool_rounds.

    Returns (assistant_text, tool_results).
    Monkeypatch this function in tests to avoid live model calls.
    """
    allowed = allowed_tools or set()
    enrollment_id = enrollment_id_from_state(state)
    tool_results: list[dict[str, Any]] = []
    declarations = _declarations_for(allowed)

    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=user_message)]),
    ]

    config_kwargs: dict[str, Any] = {
        "system_instruction": system_prompt,
        "max_output_tokens": max_tokens,
    }
    if declarations:
        config_kwargs["tools"] = [types.Tool(function_declarations=declarations)]

    for _ in range(max(1, max_tool_rounds)):
        resp = await gemini_client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        # Collect function calls from candidates
        fn_calls: list[tuple[str, dict[str, Any], str | None]] = []
        text_parts: list[str] = []
        model_parts: list[types.Part] = []

        candidates = getattr(resp, "candidates", None) or []
        for cand in candidates:
            content = getattr(cand, "content", None)
            if content is None:
                continue
            for part in getattr(content, "parts", None) or []:
                model_parts.append(part)
                fc = getattr(part, "function_call", None)
                if fc is not None and getattr(fc, "name", None):
                    raw_args = getattr(fc, "args", None) or {}
                    if isinstance(raw_args, dict):
                        args = dict(raw_args)
                    else:
                        try:
                            args = dict(raw_args)
                        except Exception:
                            args = {}
                    fn_calls.append((fc.name, args, getattr(fc, "id", None)))
                elif getattr(part, "text", None):
                    text_parts.append(part.text)

        if not fn_calls:
            text = "".join(text_parts) or (getattr(resp, "text", None) or "")
            return text, tool_results

        # Append model turn, then tool responses
        contents.append(types.Content(role="model", parts=model_parts))
        response_parts: list[types.Part] = []
        for name, args, call_id in fn_calls:
            result = await _dispatch_tool(name, args, enrollment_id, allowed)
            entry = {"tool": name, "args": args, "result": result}
            tool_results.append(entry)
            # Apply successful profile writes into a lightweight note for the model
            fr_kwargs: dict[str, Any] = {
                "name": name,
                "response": {"result": result},
            }
            if call_id:
                fr_kwargs["id"] = call_id
            response_parts.append(
                types.Part(function_response=types.FunctionResponse(**fr_kwargs))
            )
        contents.append(types.Content(role="user", parts=response_parts))

    # Exhausted rounds — last model text or empty
    return "", tool_results


async def run_node_llm_simple(
    *,
    system_prompt: str,
    user_message: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    model: str = TEXT_MODEL,
) -> str:
    """No-tools path — reuses gemini generate_text semantics."""
    from app.providers.gemini_provider import generate_text

    return await generate_text(system_prompt, user_message, max_tokens, model)
