"""Unit tests for LangGraph tutor_session (LG-1)."""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.graphs.tutor_session.graph import compile_tutor_session_graph, thread_id_for_claims
from app.graphs.tutor_session.nodes.entry import entry_node
from app.graphs.tutor_session.nodes.router import route_after_router, router_node
from app.graphs.tutor_session.state import TutorState


def test_graph_compiles():
    graph = compile_tutor_session_graph(checkpointer=MemorySaver())
    assert graph is not None
    # Smoke: graph has expected nodes
    spec = graph.get_graph()
    node_ids = set(spec.nodes.keys())
    assert "entry" in node_ids
    assert "router" in node_ids
    assert "open_name" in node_ids
    assert "pre_assess" in node_ids


def test_entry_merges_server_context_into_profile_and_task():
    state: TutorState = {
        "mint": {
            "sub": "enrollment:enr-123",
            "server_context": {
                "courseTitle": "Intro Python",
                "profile": {"preferredName": "Sam"},
                "task": {
                    "tutorStage": "onboarding",
                    "enrollmentId": "enr-123",
                    "currentBlockId": "block-1",
                },
            },
        },
        "messages": [],
    }
    out = entry_node(state)
    assert out["profile"]["preferred_name"] == "Sam"
    assert out["task"]["tutor_stage"] == "onboarding"
    assert out["task"]["enrollment_id"] == "enr-123"
    assert out["course_title"] == "Intro Python"
    assert out["task"]["current_block_id"] == "block-1"


def test_entry_mint_overlay_wins_over_stale_checkpoint_profile():
    state: TutorState = {
        "profile": {"preferred_name": "Old"},
        "task": {"tutor_stage": "pre_assess"},
        "mint": {
            "server_context": {
                "profile": {"preferredName": "New"},
                "task": {"tutorStage": "onboarding"},
            },
        },
    }
    out = entry_node(state)
    assert out["profile"]["preferred_name"] == "New"
    assert out["task"]["tutor_stage"] == "onboarding"


def test_router_maps_pre_assess_stage():
    state: TutorState = {"task": {"tutor_stage": "pre_assess"}}
    out = router_node(state)
    assert out["route"] == "pre_assess"
    assert route_after_router({**state, **out}) == "pre_assess"


def test_router_defaults_unknown_to_open_name():
    state: TutorState = {"task": {"tutor_stage": "active"}}
    out = router_node(state)
    assert out["route"] == "open_name"
    assert route_after_router({**state, **out}) == "open_name"


def test_router_onboarding_to_open_name():
    out = router_node({"task": {"tutorStage": "onboarding"}})
    assert out["route"] == "open_name"


def test_thread_id_from_enrollment():
    claims = {
        "server_context": {"enrollmentId": "abc"},
        "jti": "j1",
    }
    assert thread_id_for_claims(claims) == "enrollment:abc"


def test_thread_id_explicit():
    assert thread_id_for_claims({"thread_id": "enrollment:x"}) == "enrollment:x"


@pytest.mark.asyncio
async def test_open_name_without_tools_returns_text(monkeypatch):
    from app.graphs.tutor_session.nodes import open_name as open_name_mod

    async def fake_llm(**kwargs):
        assert "save_profile" in (kwargs.get("allowed_tools") or set())
        return "Hi! What name should I use?", []

    monkeypatch.setattr(open_name_mod, "run_node_llm", fake_llm)

    state: TutorState = {
        "mint": {"server_context": {"courseTitle": "Py 101", "task": {"tutorStage": "onboarding"}}},
        "profile": {},
        "task": {"tutor_stage": "onboarding"},
        "messages": [],
        "tool_results": [],
    }
    # entry first
    state = {**state, **entry_node(state)}
    out = await open_name_mod.open_name_node(state)
    assert out["assistant_text"] == "Hi! What name should I use?"
    assert out["messages"][-1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_graph_ainvoke_open_name_path(monkeypatch):
    from app.graphs.tutor_session.nodes import open_name as open_name_mod
    from app.graphs.tutor_session.nodes import pre_assess as pre_assess_mod

    async def fake_open(**kwargs):
        return "Welcome to the course! What should I call you?", []

    async def fake_pre(**kwargs):
        return "First question: what is a variable?", []

    monkeypatch.setattr(open_name_mod, "run_node_llm", fake_open)
    monkeypatch.setattr(pre_assess_mod, "run_node_llm", fake_pre)

    graph = compile_tutor_session_graph(checkpointer=MemorySaver())
    result = await graph.ainvoke(
        {
            "mint": {
                "server_context": {
                    "courseTitle": "Intro",
                    "task": {"tutorStage": "onboarding", "enrollmentId": "e1"},
                },
            },
            "messages": [],
            "tool_results": [],
            "assistant_text": "",
        },
        config={"configurable": {"thread_id": "enrollment:e1"}},
    )
    assert "Welcome" in result["assistant_text"]
    assert result["route"] == "open_name"


@pytest.mark.asyncio
async def test_graph_ainvoke_pre_assess_path(monkeypatch):
    from app.graphs.tutor_session.nodes import open_name as open_name_mod
    from app.graphs.tutor_session.nodes import pre_assess as pre_assess_mod

    async def fake_open(**kwargs):
        return "should-not-run", []

    async def fake_pre(**kwargs):
        return "Let's see where you are. Ready for a quick question?", []

    monkeypatch.setattr(open_name_mod, "run_node_llm", fake_open)
    monkeypatch.setattr(pre_assess_mod, "run_node_llm", fake_pre)

    graph = compile_tutor_session_graph(checkpointer=MemorySaver())
    result = await graph.ainvoke(
        {
            "mint": {
                "server_context": {
                    "profile": {"preferredName": "Sam"},
                    "task": {"tutorStage": "pre_assess", "enrollmentId": "e2"},
                },
            },
            "messages": [{"role": "user", "content": "ready"}],
            "tool_results": [],
            "assistant_text": "",
        },
        config={"configurable": {"thread_id": "enrollment:e2"}},
    )
    assert "quick question" in result["assistant_text"]
    assert result["route"] == "pre_assess"
    assert result["profile"].get("preferred_name") == "Sam"
