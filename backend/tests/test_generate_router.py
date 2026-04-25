AUTH = {"X-API-Key": "admin-test-key"}


def test_generate_questions_valid_body(client):
    resp = client.post("/generate/questions", json={
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "target_syntactic_trap_key": "none",
        "difficulty_overall": "medium",
    }, headers=AUTH)
    assert resp.status_code in (200, 500)


def test_generate_compare_valid_body(client):
    resp = client.post("/generate/questions/compare", json={
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "providers": ["anthropic"],
    }, headers=AUTH)
    assert resp.status_code in (200, 500)


def test_generate_run_invalid_uuid(client):
    resp = client.get("/generate/runs/not-a-uuid", headers=AUTH)
    assert resp.status_code == 400


def test_generate_run_not_found(client):
    resp = client.get(
        "/generate/runs/00000000-0000-0000-0000-000000000000",
        headers=AUTH,
    )
    assert resp.status_code == 404


def test_generate_question_custom_provider_accepted(client):
    """provider_name/model_name in body are accepted (not 422)."""
    resp = client.post(
        "/generate/questions",
        headers={**AUTH, "Content-Type": "application/json"},
        json={
            "target_grammar_role_key": "agreement",
            "target_grammar_focus_key": "subject_verb_agreement",
            "provider_name": "openai",
            "model_name": "gpt-4o",
        },
    )
    assert resp.status_code != 422


def test_generate_question_without_provider_uses_default(client):
    """Omitting provider_name/model_name still succeeds (uses settings defaults)."""
    resp = client.post(
        "/generate/questions",
        headers={**AUTH, "Content-Type": "application/json"},
        json={
            "target_grammar_role_key": "agreement",
            "target_grammar_focus_key": "subject_verb_agreement",
        },
    )
    assert resp.status_code != 422