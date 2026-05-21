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


def test_generate_question_reading_request_accepted(client):
    resp = client.post(
        "/generate/questions",
        headers={**AUTH, "Content-Type": "application/json"},
        json={
            "target_reading_skill_family_key": "words_in_context",
            "target_reading_focus_key": "figurative_language_meaning",
            "target_test_construct_key": "figurative_interpretation_precision",
            "difficulty_overall": "medium",
        },
    )
    assert resp.status_code != 422


def test_generate_question_without_domain_target_rejected(client):
    resp = client.post(
        "/generate/questions",
        headers={**AUTH, "Content-Type": "application/json"},
        json={"difficulty_overall": "medium"},
    )
    assert resp.status_code == 422


def test_source_set_operational_keys_filter_strips_all_operational():
    """Identity invariant: `generation_source_set` is the request payload
    with `_SOURCE_SET_OPERATIONAL_KEYS` stripped. Lineage keys (content
    spec, source IDs) must survive; operational keys (provider, model,
    seed, retry, batch workflow) must be removed.
    """
    from app.routers.generate import _SOURCE_SET_OPERATIONAL_KEYS

    expected_operational = {
            "provider_name", "model_name", "seed", "temperature",
            "retry_attempt", "idempotency_key", "derived_from_question_id",
            "requested_count", "requested_by", "student_id",
            "requested_by_user_token", "release_policy", "skip_review",
        }
    assert _SOURCE_SET_OPERATIONAL_KEYS == expected_operational, (
        "Operational keys set drifted from the locked Phase 0 filter; "
        "see TASKS_GENERATION.md `## Locked Decisions` -> Request Payload "
        "Layering."
    )

    request_data = {
        # Lineage (must survive)
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "target_syntactic_trap_key": "none",
        "difficulty_overall": "medium",
        "source_question_ids": ["q-1", "q-2"],
        # Operational (must be stripped)
        "provider_name": "anthropic",
        "model_name": "claude-sonnet-4-6",
        "seed": 42,
        "temperature": 0.7,
        "retry_attempt": 1,
        "idempotency_key": "client-abc",
        "requested_count": 5,
        "requested_by": "admin",
        "student_id": 17,
        "requested_by_user_token": "00000000-0000-0000-0000-000000000000",
        "release_policy": "admin_review_required",
        "skip_review": True,
    }

    filtered = {
        k: v for k, v in request_data.items() if k not in _SOURCE_SET_OPERATIONAL_KEYS
    }

    assert filtered == {
        "target_grammar_role_key": "agreement",
        "target_grammar_focus_key": "subject_verb_agreement",
        "target_syntactic_trap_key": "none",
        "difficulty_overall": "medium",
        "source_question_ids": ["q-1", "q-2"],
    }
    assert not (set(filtered) & _SOURCE_SET_OPERATIONAL_KEYS)
