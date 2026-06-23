"""TASK-B0A — diagnostic domain classification + question-pool query.

Covers bug-761: reading is classified via ``skill_family_key`` (singular), not
``reading_skill_family_key`` (NULL on the whole live v8 bank).

DB-free: ``derive_domain`` is pure; ``build_pool_stmt`` is asserted by compiling the
statement to SQL and inspecting the rendered predicates.
"""

from sqlalchemy.dialects import postgresql

from app.diagnostic.queries import derive_domain, build_pool_stmt


def _sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


# ── derive_domain ────────────────────────────────────────────────────────────

def test_derive_domain_reading_via_skill_family_key():
    assert derive_domain({"skill_family_key": "inferences"}) == "reading"


def test_derive_domain_grammar_via_grammar_role_key():
    assert derive_domain({"grammar_role_key": "punctuation"}) == "grammar"


def test_derive_domain_none_when_neither():
    assert derive_domain({"stem_type_key": "complete_the_text"}) is None
    assert derive_domain({}) is None
    assert derive_domain(None) is None


def test_derive_domain_ignores_legacy_reading_skill_family_key():
    # The legacy field is NULL in the bank; even if present it is not how we classify.
    assert derive_domain({"reading_skill_family_key": "inferences"}) is None


def test_derive_domain_reading_takes_precedence_if_both_present():
    # Defensive: documented precedence (no overlap exists in the real bank).
    ann = {"skill_family_key": "inferences", "grammar_role_key": "punctuation"}
    assert derive_domain(ann) == "reading"


# ── build_pool_stmt ──────────────────────────────────────────────────────────

def test_pool_reading_filters_skill_family_key_not_legacy():
    sql = _sql(build_pool_stmt(domain="reading", skill_family_key="inferences"))
    assert "skill_family_key" in sql
    assert "inferences" in sql
    assert "reading_skill_family_key" not in sql
    assert "reading_focus_key" not in sql


def test_pool_grammar_filters_grammar_role_key():
    sql = _sql(build_pool_stmt(domain="grammar", grammar_role_key="punctuation"))
    assert "grammar_role_key" in sql
    assert "punctuation" in sql


def test_pool_always_restricts_active_and_excludes_dry_run():
    sql = _sql(build_pool_stmt())
    assert "practice_status" in sql and "active" in sql
    assert "dry_run" in sql  # dry-run release policy exclusion


def test_pool_difficulty_filter_only_when_provided():
    with_diff = _sql(build_pool_stmt(domain="grammar", grammar_role_key="punctuation", difficulty="low"))
    assert "difficulty_overall" in with_diff and "low" in with_diff

    without_diff = _sql(build_pool_stmt(domain="grammar", grammar_role_key="punctuation"))
    assert "difficulty_overall" not in without_diff


def test_pool_excludes_seen_user_and_chosen_ids():
    sql = _sql(
        build_pool_stmt(
            domain="reading",
            skill_family_key="inferences",
            exclude_question_ids=["11111111-1111-1111-1111-111111111111"],
            exclude_seen_user_id=42,
        )
    )
    assert "user_progress" in sql.lower()        # seen-exclusion subquery present
    assert "11111111-1111-1111-1111-111111111111" in sql
    assert "NOT IN" in sql.upper()
