"""TASK-028 — _fallback_passage_tokens priority chain tests.

Pins the precedence used to build student highlight tokens:
  Step 0: annotation.passage_spans.tokens  (Pass 3 — word-level)  ← wins
  Step 1: ann_data["passage_tokens"]       (old Pass 2 tokens)
  Step 2+: synthetic span matching          (only if neither present)

Three tests cover the priority chain — specifically that Pass 3
passage_spans wins over the old passage_tokens even when both exist.

Pure unit tests — _fallback_passage_tokens is a sync function with no
DB or LLM. Question / QuestionAnnotation are duck-typed via SimpleNamespace.
"""
import os

# Force env before any app imports (see conftest.py)
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test"
)
os.environ.setdefault("ADMIN_API_KEYS", "admin-test-key")
os.environ.setdefault("STUDENT_API_KEYS", "student-test-key")

import sys
from types import SimpleNamespace

sys.path.insert(0, "/home/jb/DSAT_REDUX_MD/backend")

from app.routers.student import _fallback_passage_tokens


# ---------------------------------------------------------------------------
# Shared fakes
# ---------------------------------------------------------------------------

# Pass 3 word-level tokens as written by annotate_spans() to passage_spans
PASS3_SPANS = {
    "label": "SVA: subject + main_verb",
    "anatomy_present": ["subject", "main_verb"],
    "concepts_present": ["subject_verb_agreement"],
    "tokens": [
        {"text": "The ", "anatomy": ["determiner"], "concept_tags": [], "is_blank": False},
        {"text": "cat", "anatomy": ["subject"], "concept_tags": [], "is_blank": False},
        {"text": "sat", "anatomy": ["main_verb"],
         "concept_tags": ["subject_verb_agreement"], "is_blank": False},
    ],
}

# Old Pass 2 flat token dicts — different shape (no anatomy/concept_tags split)
OLD_PASS2_TOKENS = [
    {"text": "The cat sat", "tags": ["subject", "main_verb"]},
]


def _q():
    # question is only touched in the synthetic path (Step 2+); for these
    # priority tests it is never reached, so a bare namespace is enough.
    return SimpleNamespace(current_passage_text="The cat sat.")


# ---------------------------------------------------------------------------
# 1. passage_spans (Pass 3) wins over old passage_tokens
# ---------------------------------------------------------------------------

class TestPassageSpansWins:
    def test_pass3_spans_preferred_when_both_present(self):
        """When annotation has passage_spans.tokens AND ann_data has old
        passage_tokens, the Pass 3 spans win and are returned transformed."""
        question = _q()
        ann_data = {"passage_tokens": OLD_PASS2_TOKENS}
        annotation = SimpleNamespace(passage_spans=PASS3_SPANS)

        result = _fallback_passage_tokens(question, ann_data, annotation=annotation)

        # Returned the 3 Pass 3 tokens, NOT the 1 old Pass 2 token
        assert result is not None
        assert len(result) == 3
        # Transformation: merged tags = anatomy + concept_tags, all fields present
        sat = result[2]
        assert sat["text"] == "sat"
        assert sat["tags"] == ["main_verb", "subject_verb_agreement"]
        assert sat["anatomy"] == ["main_verb"]
        assert sat["concept_tags"] == ["subject_verb_agreement"]
        assert sat["is_blank"] is False
        # The old passage_tokens shape (single dict) was NOT returned
        assert result != OLD_PASS2_TOKENS


# ---------------------------------------------------------------------------
# 2. Old Pass 2 passage_tokens used when no passage_spans
# ---------------------------------------------------------------------------

class TestOldPassageTokensFallback:
    def test_pass2_tokens_returned_when_no_passage_spans(self):
        """When annotation is None (or has no passage_spans), the old
        ann_data passage_tokens are returned unchanged."""
        question = _q()
        ann_data = {"passage_tokens": OLD_PASS2_TOKENS}

        # annotation=None
        result_none = _fallback_passage_tokens(question, ann_data, annotation=None)
        assert result_none == OLD_PASS2_TOKENS

        # annotation present but passage_spans is None
        annotation_empty = SimpleNamespace(passage_spans=None)
        result_empty = _fallback_passage_tokens(
            question, ann_data, annotation=annotation_empty
        )
        assert result_empty == OLD_PASS2_TOKENS


# ---------------------------------------------------------------------------
# 3. passage_spans present but tokens empty → falls through to old tokens
# ---------------------------------------------------------------------------

class TestEmptyPassageSpansFallthrough:
    def test_empty_tokens_falls_through_to_pass2(self):
        """Edge of the priority chain: passage_spans exists but its `tokens`
        list is empty. The `if tokens:` guard must NOT return [] — it must
        fall through to the old passage_tokens so students still get a
        highlight instead of an empty one."""
        question = _q()
        ann_data = {"passage_tokens": OLD_PASS2_TOKENS}
        annotation = SimpleNamespace(
            passage_spans={"label": "x", "anatomy_present": [], "tokens": []}
        )

        result = _fallback_passage_tokens(question, ann_data, annotation=annotation)

        assert result == OLD_PASS2_TOKENS
        assert result != []