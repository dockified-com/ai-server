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


def test_tutor_open_asks_for_name_when_unknown():
    msg = build_user_message(
        "tutor_open",
        {"courseTitle": "Intro Python", "lessonTitle": "Variables"},
        {},
    )
    assert "Intro Python" in msg
    assert "Variables" in msg
    assert "name they want you to use" in msg
    assert "Do not teach concepts yet" in msg


def test_tutor_open_greets_known_preferred_name():
    msg = build_user_message(
        "tutor_open",
        {
            "course_title": "CS101",
            "lesson_title": "Loops",
            "preferredName": "Alex",
        },
        {},
    )
    assert "CS101" in msg
    assert "Alex" in msg
    assert "already known" in msg
    assert "Do not teach yet" in msg


def test_pre_assess_uses_topics_message_and_prior_turns():
    msg = build_user_message(
        "pre_assess",
        {
            "preferred_name": "Sam",
            "topics": ["variables", "loops"],
            "recentTurns": [
                {"role": "assistant", "text": "What is a variable?"},
                {"role": "user", "userInput": "A named box"},
            ],
        },
        {"message": "I think so"},
    )
    assert "Student name: Sam" in msg
    assert "variables, loops" in msg
    assert "What is a variable?" in msg
    assert "A named box" in msg
    assert "Student message: I think so" in msg
    assert "beginner|intermediate|advanced" in msg


def test_pre_assess_session_start_without_message():
    msg = build_user_message(
        "pre_assess",
        {"preferredName": "Jo", "lesson_objectives": ["lists"]},
        {},
    )
    assert "Student name: Jo" in msg
    assert "lists" in msg
    assert "session just started" in msg


def test_final_clarify_wording_only_message():
    msg = build_user_message(
        "final_clarify",
        {"challenge_prompt": "Write a function that reverses a string"},
        {"question": "Does reverse mean in-place?"},
    )
    assert "Write a function that reverses a string" in msg
    assert "Does reverse mean in-place?" in msg
    assert "No hints, no code, no strategy" in msg


def test_tts_builder_is_safe_placeholder():
    msg = build_user_message("tts", {}, {})
    assert "TTS" in msg
    assert isinstance(msg, str)
    assert len(msg) > 0


def test_unknown_stream_agent_falls_back_without_crash():
    msg = build_user_message("future_agent", {"user_message": "hi"}, {})
    assert msg == "hi"
    msg2 = build_user_message("future_agent", {}, {})
    assert msg2 == "Continue."
