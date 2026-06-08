from app.runtime.reasoning import build_user_message


def test_socratic_message_uses_client_and_server_context():
    msg = build_user_message(
        agent="socratic",
        server_context={"problem_prompt": "Sum a list"},
        client_context={"student_code": "print(1)", "stdout": "1", "stderr": "", "attempt_count": 2},
    )
    assert "Sum a list" in msg
    assert "print(1)" in msg


def test_socratic_escalates_guidance_tier():
    early = build_user_message(
        "socratic", {"problem_prompt": "p"}, {"student_code": "c", "attempt_count": 1}
    )
    late = build_user_message(
        "socratic", {"problem_prompt": "p"}, {"student_code": "c", "attempt_count": 6}
    )
    assert "high-level conceptual" in early
    assert "analogous simpler example" in late


def test_understanding_message_uses_rubric_and_response():
    msg = build_user_message(
        "understanding-check",
        {"rubric": "Explain recursion"},
        {"response": "It calls itself", "attempt_number": 1},
    )
    assert "Explain recursion" in msg
    assert "It calls itself" in msg


def test_ask_message_includes_chunks():
    msg = build_user_message(
        agent="ask",
        server_context={"chunks": ["chunk-A", "chunk-B"], "block_context": None},
        client_context={"question": "what is recursion?"},
    )
    assert "chunk-A" in msg
    assert "what is recursion?" in msg
