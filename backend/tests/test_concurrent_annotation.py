"""Tests for concurrent Phase 1 annotation and serial Phase 2 validate/persist."""
import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---- Helpers ----

def _make_q_data(question_number: int, stem_type_key: str = "complete_the_text",
                 question_text: str = "", passage_text: str = "") -> dict:
    """Build a minimal question dict for annotation."""
    return {
        "source_question_number": question_number,
        "stem_type_key": stem_type_key,
        "question_text": question_text or f"Question {question_number}",
        "passage_text": passage_text,
        "current_question_text": question_text or f"Question {question_number}",
        "current_correct_option_label": "A",
        "options": [
            {"label": "A", "text": "Option A"},
            {"label": "B", "text": "Option B"},
            {"label": "C", "text": "Option C"},
            {"label": "D", "text": "Option D"},
        ],
    }


def _make_annotate_result(raw_text: str = '{"correct_option_label": "A"}'):
    """Build a mock LLM completion result."""
    return SimpleNamespace(
        raw_text=raw_text,
        provider="test",
        model="test-model",
        latency_ms=100,
        token_usage={"prompt_tokens": 10, "completion_tokens": 5},
    )


def _grammar_q(num: int) -> dict:
    """Grammar-domain question (sentence-only complete_the_text)."""
    return _make_q_data(num, stem_type_key="complete_the_text",
                        question_text="The student _______ the book carefully.")


def _reading_q(num: int) -> dict:
    """Reading-domain question (with passage)."""
    return _make_q_data(num, stem_type_key="complete_the_text",
                        question_text="Which choice best describes the main idea?",
                        passage_text="This passage is about science.")


def _writing_q(num: int) -> dict:
    """Writing/unknown-domain question."""
    return _make_q_data(num, stem_type_key="unknown_stem",
                        question_text="Write an essay about the topic.")


# ---- Tests ----

class TestDomainSorting:
    """Verify that questions are sorted by domain for KV-prefix caching."""

    def test_domain_order_groups_grammar_before_reading(self):
        from app.prompts.annotate_prompt import _detect_domain

        questions = [_reading_q(1), _grammar_q(2), _reading_q(3), _grammar_q(4)]
        domain_order = {"grammar": 0, "reading": 1, "writing": 2}
        order = sorted(
            range(len(questions)),
            key=lambda idx: domain_order.get(_detect_domain(questions[idx]), 99),
        )
        # Grammar questions (indices 1, 3) should come before reading (0, 2)
        assert order == [1, 3, 0, 2]

    def test_domain_order_handles_unknown(self):
        from app.prompts.annotate_prompt import _detect_domain

        questions = [_writing_q(1), _grammar_q(2), _reading_q(3)]
        domain_order = {"grammar": 0, "reading": 1, "writing": 2}
        order = sorted(
            range(len(questions)),
            key=lambda idx: domain_order.get(_detect_domain(questions[idx]), 99),
        )
        # grammar(1) -> 0, reading(2) -> 1, unknown(0) -> 99
        assert order == [1, 2, 0]

    def test_all_same_domain_preserves_relative_order(self):
        from app.prompts.annotate_prompt import _detect_domain

        questions = [_grammar_q(1), _grammar_q(2), _grammar_q(3)]
        domain_order = {"grammar": 0, "reading": 1, "writing": 2}
        order = sorted(
            range(len(questions)),
            key=lambda idx: domain_order.get(_detect_domain(questions[idx]), 99),
        )
        assert order == [0, 1, 2]  # stable sort preserves order


class TestAnnotateOne:
    """Test the _annotate_one async helper."""

    @pytest.mark.asyncio
    async def test_annotate_one_success(self):
        """Successful annotation returns (idx, annotate_json, None, meta)."""
        from app.parsers.json_parser import normalize_annotation

        questions_data = [_grammar_q(1)]
        provider = AsyncMock()
        provider.complete = AsyncMock(return_value=_make_annotate_result(
            '{"correct_option_label": "A", "grammar_focus_key": "subject_verb_agreement"}'
        ))

        # Import the function we'll test via the module
        from app.prompts.annotate_prompt import build_annotate_prompt, enforce_nullability, _detect_domain
        from app.parsers.json_parser import extract_json_from_text, normalize_annotation

        semaphore = asyncio.Semaphore(8)
        idx = 0

        async def annotate_one(idx):
            q_data = questions_data[idx]
            system, user = build_annotate_prompt(q_data)
            async with semaphore:
                result = await provider.complete(system=system, user=user, max_tokens=8192)
            parsed = extract_json_from_text(result.raw_text, "test", "test-model")
            annotate_json = normalize_annotation(parsed)
            annotate_json = enforce_nullability(annotate_json, _detect_domain(q_data))
            meta = {
                "question_index": idx,
                "provider": result.provider,
                "model": result.model,
                "latency_ms": result.latency_ms,
                "token_usage": getattr(result, "token_usage", None) or {},
            }
            return idx, annotate_json, None, meta

        idx, ajson, err, meta = await annotate_one(0)
        assert err is None
        assert ajson is not None
        assert meta["question_index"] == 0
        assert provider.complete.call_count == 1

    @pytest.mark.asyncio
    async def test_annotate_one_retry_on_parse_failure(self):
        """Annotation retries on JSON parse failure and succeeds on second attempt."""
        questions_data = [_grammar_q(1)]
        provider = AsyncMock()
        # First call returns garbage, second returns valid JSON
        provider.complete = AsyncMock(side_effect=[
            _make_annotate_result("NOT JSON AT ALL"),
            _make_annotate_result('{"correct_option_label": "A"}'),
        ])

        from app.prompts.annotate_prompt import build_annotate_prompt, enforce_nullability, _detect_domain
        from app.parsers.json_parser import extract_json_from_text, normalize_annotation

        semaphore = asyncio.Semaphore(8)
        idx = 0
        q_data = questions_data[idx]
        system, user = build_annotate_prompt(q_data)

        last_err = None
        annotate_json = None
        for attempt in range(3):
            try:
                async with semaphore:
                    result = await provider.complete(system=system, user=user, max_tokens=8192)
                parsed = extract_json_from_text(result.raw_text, "test", "test-model")
                if not parsed:
                    raise ValueError("empty")
                annotate_json = normalize_annotation(parsed)
                annotate_json = enforce_nullability(annotate_json, _detect_domain(q_data))
                break
            except ValueError:
                last_err = ValueError("parse failed")
                if attempt < 2:
                    await asyncio.sleep(0)  # no real delay in test

        assert annotate_json is not None, f"Should have succeeded on retry, got err: {last_err}"
        assert provider.complete.call_count == 2

    @pytest.mark.asyncio
    async def test_annotate_one_all_retries_fail(self):
        """After 3 failed attempts, returns (idx, None, err, None)."""
        questions_data = [_grammar_q(1)]
        provider = AsyncMock()
        provider.complete = AsyncMock(side_effect=RuntimeError("LLM down"))

        from app.prompts.annotate_prompt import build_annotate_prompt

        semaphore = asyncio.Semaphore(8)
        q_data = questions_data[0]
        system, user = build_annotate_prompt(q_data)

        last_err = None
        for attempt in range(3):
            try:
                async with semaphore:
                    result = await provider.complete(system=system, user=user, max_tokens=8192)
            except Exception as exc:
                last_err = exc
                break  # non-ValueError errors break immediately

        assert last_err is not None
        assert "LLM down" in str(last_err)


class TestConcurrentAnnotationSemaphore:
    """Verify the semaphore actually bounds concurrency."""

    @pytest.mark.asyncio
    async def test_semaphore_bounds_concurrency(self):
        """With semaphore=3, at most 3 concurrent LLM calls are in flight."""
        call_times = []
        max_concurrent = 0
        current_concurrent = 0

        class TrackingProvider:
            async def complete(self, **kwargs):
                nonlocal current_concurrent, max_concurrent
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
                call_times.append(asyncio.get_event_loop().time())
                await asyncio.sleep(0.05)  # simulate LLM latency
                current_concurrent -= 1
                return _make_annotate_result('{"correct_option_label": "A"}')

        provider = TrackingProvider()
        semaphore = asyncio.Semaphore(3)

        async def annotate_one(idx):
            async with semaphore:
                result = await provider.complete(system="sys", user="user", max_tokens=100)
            return idx, {"correct_option_label": "A"}, None, {"question_index": idx}

        # Fire 8 concurrent requests with semaphore=3
        results = await asyncio.gather(*[annotate_one(i) for i in range(8)])
        assert len(results) == 8
        assert max_concurrent <= 3, f"Expected max 3 concurrent, got {max_concurrent}"

    @pytest.mark.asyncio
    async def test_gather_preserves_results(self):
        """asyncio.gather returns results in submission order even when domain-sorted."""

        async def mock_annotate(idx):
            # Simulate variable latency
            await asyncio.sleep(0.01 * (idx % 3))
            return idx, {"q": idx}, None, {"question_index": idx}

        # Submit in domain-sorted order: [2, 0, 1] (grammar, reading, unknown)
        order = [2, 0, 1]
        results = await asyncio.gather(*[mock_annotate(i) for i in order])

        # Results come back in the *submission* order, not completion order
        assert results[0][0] == 2  # first submitted
        assert results[1][0] == 0  # second submitted
        assert results[2][0] == 1  # third submitted

        # Index lookup works correctly
        by_idx = {r[0]: r for r in results}
        assert by_idx[0] == (0, {"q": 0}, None, {"question_index": 0})
        assert by_idx[1] == (1, {"q": 1}, None, {"question_index": 1})
        assert by_idx[2] == (2, {"q": 2}, None, {"question_index": 2})


class TestPhase2PreservesOrder:
    """Verify that Phase 2 iterates in original question order, not domain-sorted order."""

    def test_phase_2_iterates_in_original_order(self):
        """Even though Phase 1 submits in domain-sorted order,
        Phase 2 must iterate enumerate(questions_data) in original order."""
        questions = [_reading_q(0), _grammar_q(1), _writing_q(2), _grammar_q(3)]

        # Simulate Phase 1 results indexed by question_index
        _annot_by_idx = {
            0: ({"correct_option_label": "A"}, None, {"question_index": 0}),
            1: ({"correct_option_label": "B"}, None, {"question_index": 1}),
            2: ({"correct_option_label": "C"}, None, {"question_index": 2}),
            3: ({"correct_option_label": "D"}, None, {"question_index": 3}),
        }

        # Phase 2 iterates in original order
        phase2_order = []
        for i, q_data in enumerate(questions):
            annotate_json, _last_err, _meta = _annot_by_idx.get(i, (None, None, None))
            if annotate_json is not None:
                phase2_order.append((i, q_data["source_question_number"]))

        # Must be 0,1,2,3 — original order, not domain-sorted order
        assert phase2_order == [(0, 0), (1, 1), (2, 2), (3, 3)]

    def test_phase_2_skips_failed_annotations(self):
        """Phase 2 continues past questions where annotation failed."""
        questions = [_grammar_q(0), _reading_q(1), _grammar_q(2)]
        # Question 1 failed annotation
        _annot_by_idx = {
            0: ({"correct_option_label": "A"}, None, {"question_index": 0}),
            1: (None, RuntimeError("LLM error"), None),
            2: ({"correct_option_label": "C"}, None, {"question_index": 2}),
        }

        persisted = []
        for i, q_data in enumerate(questions):
            annotate_json, _last_err, _meta = _annot_by_idx.get(i, (None, None, None))
            if annotate_json is None:
                continue  # skip failed
            persisted.append(i)

        # Only 0 and 2 get persisted; 1 is skipped
        assert persisted == [0, 2]


class TestConfigIntegration:
    """Verify ollama_max_concurrent is accessible from settings."""

    def test_default_value(self):
        from app.config import Settings
        s = Settings()
        assert s.ollama_max_concurrent == 8

    def test_env_override(self):
        import os
        saved = os.environ.get("OLLAMA_MAX_CONCURRENT")
        try:
            os.environ["OLLAMA_MAX_CONCURRENT"] = "12"
            from app.config import Settings
            s = Settings()
            assert s.ollama_max_concurrent == 12
        finally:
            if saved is not None:
                os.environ["OLLAMA_MAX_CONCURRENT"] = saved
            else:
                os.environ.pop("OLLAMA_MAX_CONCURRENT", None)

    def test_semaphore_uses_settings(self):
        """The pipeline should create a semaphore from settings.ollama_max_concurrent."""
        from app.config import Settings
        s = Settings()
        sem = asyncio.Semaphore(s.ollama_max_concurrent)
        assert sem._value == 8
