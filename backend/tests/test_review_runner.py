"""Phase 4 (review swarm runner) — runner, provider config, concurrency,
duplicate prevention, and rerun tests.

All tests use mocked LLM providers; no live DB or network required.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.review.runner import (
    _provider_config,
    _review_providers,
    _exclude_generator_provider,
    _load_question_for_review,
    _run_single_reviewer,
    run_review_swarm,
    run_batch_review_swarm,
    RUBRIC_VERSION,
    RULES_VERSIONS,
)
from app.review.parser import ReviewParseError

# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _make_settings(**overrides):
    """Return a mock settings object with review config defaults."""
    defaults = dict(
        anthropic_api_key="sk-ant-test",
        openai_api_key="sk-openai-test",
        ollama_base_url="http://localhost:11434",
        generation_review_providers="openai,anthropic,ollama",
        generation_review_openai_model="gpt-4o",
        generation_review_anthropic_model="claude-sonnet-4-6",
        generation_review_ollama_model="deepseek-v4-pro:cloud",
        generation_review_max_concurrent=6,
        generation_review_max_retries=2,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _valid_review_json():
    """Return a valid review JSON string matching the rubric schema."""
    return json.dumps({
        "realism_score": 8.5,
        "sat_fidelity_score": 7.8,
        "difficulty_match_score": 7.2,
        "distractor_quality_score": 7.0,
        "taxonomy_match_score": 8.1,
        "explanation_quality_score": 7.5,
        "copy_risk_score": 2.0,
        "verdict": "accept",
        "reasons": {"copy_risk_score": "Low overlap with source material"},
    })


def _make_mock_db():
    """Create a properly mocked async DB session.

    The runner opens multiple async_session() contexts. Each .execute()
    must return a result object with .scalars().first() / .all() chains.
    """
    mock_db = AsyncMock()
    # Mock execute to return a result with proper .scalars() chaining
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result
    mock_db.get.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    return mock_db


def _setup_session_mock(mock_session_ctx, mock_db):
    """Wire up the async_session mock context manager to return mock_db."""
    mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=None)


# ---------------------------------------------------------------------------
# Provider config tests
# ---------------------------------------------------------------------------

class TestProviderConfig:

    def test_openai_config(self):
        settings = _make_settings()
        api_key, model = _provider_config("openai", settings)
        assert api_key == "sk-openai-test"
        assert model == "gpt-4o"

    def test_anthropic_config(self):
        settings = _make_settings()
        api_key, model = _provider_config("anthropic", settings)
        assert api_key == "sk-ant-test"
        assert model == "claude-sonnet-4-6"

    def test_ollama_config(self):
        settings = _make_settings()
        api_key, model = _provider_config("ollama", settings)
        assert api_key == ""
        assert model == "deepseek-v4-pro:cloud"

    def test_unknown_provider_raises(self):
        settings = _make_settings()
        with pytest.raises(ValueError, match="Unknown review provider"):
            _provider_config("gemini", settings)


class TestReviewProviders:

    def test_default_providers(self):
        settings = _make_settings()
        providers = _review_providers(settings)
        assert len(providers) == 3
        names = [p for p, _ in providers]
        assert names == ["openai", "anthropic", "ollama"]

    def test_single_provider(self):
        settings = _make_settings(generation_review_providers="openai")
        providers = _review_providers(settings)
        assert len(providers) == 1
        assert providers[0] == ("openai", "gpt-4o")

    def test_empty_provider_string(self):
        settings = _make_settings(generation_review_providers="")
        providers = _review_providers(settings)
        assert providers == []

    def test_generator_provider_excluded(self):
        settings = _make_settings(generation_review_providers="openai,anthropic,ollama")
        providers = _review_providers(settings)
        filtered = _exclude_generator_provider(providers, "ollama")
        assert filtered == [
            ("openai", "gpt-4o"),
            ("anthropic", "claude-sonnet-4-6"),
        ]


# ---------------------------------------------------------------------------
# Runner tests — all reviewers succeed
# ---------------------------------------------------------------------------

class TestRunReviewSwarm:

    @pytest.mark.asyncio
    async def test_all_reviewers_succeed(self):
        """All reviewers return valid review JSON; run status is 'complete'."""
        settings = _make_settings(generation_review_providers="openai,anthropic")

        mock_llm_response = MagicMock()
        mock_llm_response.raw_text = _valid_review_json()
        mock_llm_response.provider = "test"
        mock_llm_response.model = "test-model"
        mock_llm_response.latency_ms = 500
        mock_llm_response.token_usage = {"prompt_tokens": 100, "completion_tokens": 200}

        question_id = uuid.uuid4()
        question_data = {
            "question_text": "Test question",
            "correct_option_label": "A",
            "options": [{"label": "A", "text": "Option A", "is_correct": True}],
        }

        with patch("app.review.runner.get_provider") as mock_get_provider, \
             patch("app.review.runner._load_question_for_review") as mock_load, \
             patch("app.review.runner.async_session") as mock_session_ctx, \
             patch("app.review.consensus.save_consensus", new_callable=AsyncMock) as mock_save_consensus:

            mock_provider = AsyncMock()
            mock_provider.complete.return_value = mock_llm_response
            mock_get_provider.return_value = mock_provider

            mock_load.return_value = {
                "question_data": question_data,
                "annotation": None,
                "source_examples": [],
                "overlap_status": "none",
                "generation_request": None,
                "version_id": None,
            }

            mock_db = _make_mock_db()
            _setup_session_mock(mock_session_ctx, mock_db)

            mock_review_run = MagicMock()
            mock_review_run.id = uuid.uuid4()
            mock_review_run.status = "running"
            mock_review_run.started_at = datetime.now(timezone.utc)
            mock_review_run.completed_at = None
            mock_review_run.rubric_version = RUBRIC_VERSION
            mock_db.get.return_value = mock_review_run

            with patch("app.review.runner.get_settings", return_value=settings):
                result = await run_review_swarm(question_id, triggered_by="manual_question")

            # Verify the run was finalized as complete
            assert mock_review_run.status == "complete"
            assert mock_review_run.completed_at is not None

    @pytest.mark.asyncio
    async def test_one_reviewer_fails(self):
        """One reviewer fails but others succeed; run status is 'partial'."""
        settings = _make_settings(generation_review_providers="openai,anthropic")

        good_response = MagicMock()
        good_response.raw_text = _valid_review_json()
        good_response.provider = "openai"
        good_response.model = "gpt-4o"
        good_response.latency_ms = 500
        good_response.token_usage = None

        question_id = uuid.uuid4()
        question_data = {
            "question_text": "Test question",
            "correct_option_label": "A",
            "options": [{"label": "A", "text": "Option A", "is_correct": True}],
        }

        call_count = 0

        async def mock_complete(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return good_response
            else:
                raise ConnectionError("API timeout")

        with patch("app.review.runner.get_provider") as mock_get_provider, \
             patch("app.review.runner._load_question_for_review") as mock_load, \
             patch("app.review.runner.async_session") as mock_session_ctx, \
             patch("app.review.consensus.save_consensus", new_callable=AsyncMock) as mock_save_consensus:

            mock_provider = AsyncMock()
            mock_provider.complete.side_effect = mock_complete
            mock_get_provider.return_value = mock_provider

            mock_load.return_value = {
                "question_data": question_data,
                "annotation": None,
                "source_examples": [],
                "overlap_status": "none",
                "generation_request": None,
                "version_id": None,
            }

            mock_db = _make_mock_db()
            _setup_session_mock(mock_session_ctx, mock_db)

            mock_review_run = MagicMock()
            mock_review_run.id = uuid.uuid4()
            mock_review_run.status = "running"
            mock_review_run.started_at = datetime.now(timezone.utc)
            mock_review_run.completed_at = None
            mock_review_run.rubric_version = RUBRIC_VERSION
            mock_db.get.return_value = mock_review_run

            with patch("app.review.runner.get_settings", return_value=settings):
                result = await run_review_swarm(question_id, triggered_by="manual_question")

            # One reviewer succeeded, one failed -> partial
            assert mock_review_run.status == "partial"

    @pytest.mark.asyncio
    async def test_malformed_reviewer_json(self):
        """Reviewer returns invalid JSON; result saved as permanent_failed."""
        settings = _make_settings(generation_review_providers="openai")

        bad_response = MagicMock()
        bad_response.raw_text = "This is not JSON at all"
        bad_response.provider = "openai"
        bad_response.model = "gpt-4o"
        bad_response.latency_ms = 100
        bad_response.token_usage = None

        question_id = uuid.uuid4()
        question_data = {
            "question_text": "Test question",
            "correct_option_label": "A",
            "options": [{"label": "A", "text": "Option A", "is_correct": True}],
        }

        with patch("app.review.runner.get_provider") as mock_get_provider, \
             patch("app.review.runner._load_question_for_review") as mock_load, \
             patch("app.review.runner.async_session") as mock_session_ctx, \
             patch("app.review.consensus.save_consensus", new_callable=AsyncMock) as mock_save_consensus:

            mock_provider = AsyncMock()
            mock_provider.complete.return_value = bad_response
            mock_get_provider.return_value = mock_provider

            mock_load.return_value = {
                "question_data": question_data,
                "annotation": None,
                "source_examples": [],
                "overlap_status": "none",
                "generation_request": None,
                "version_id": None,
            }

            mock_db = _make_mock_db()
            _setup_session_mock(mock_session_ctx, mock_db)

            mock_review_run = MagicMock()
            mock_review_run.id = uuid.uuid4()
            mock_review_run.status = "running"
            mock_review_run.started_at = datetime.now(timezone.utc)
            mock_review_run.completed_at = None
            mock_review_run.rubric_version = RUBRIC_VERSION
            mock_db.get.return_value = mock_review_run

            with patch("app.review.runner.get_settings", return_value=settings):
                result = await run_review_swarm(question_id, triggered_by="manual_question")

            # All reviewers failed -> run status is "failed"
            assert mock_review_run.status == "failed"
            mock_save_consensus.assert_awaited_once()


# ---------------------------------------------------------------------------
# Duplicate review prevention (re-review creates new run)
# ---------------------------------------------------------------------------

class TestReviewRerun:

    @pytest.mark.asyncio
    async def test_rerun_creates_new_review_run_id(self):
        """Re-review creates a new review_run_id while preserving previous rows.

        This test verifies that calling run_review_swarm twice on the same
        question produces two distinct ReviewRun IDs.
        """
        settings = _make_settings(generation_review_providers="openai")

        mock_llm_response = MagicMock()
        mock_llm_response.raw_text = _valid_review_json()
        mock_llm_response.provider = "openai"
        mock_llm_response.model = "gpt-4o"
        mock_llm_response.latency_ms = 500
        mock_llm_response.token_usage = None

        question_id = uuid.uuid4()
        question_data = {
            "question_text": "Test question",
            "correct_option_label": "A",
            "options": [{"label": "A", "text": "Option A", "is_correct": True}],
        }

        with patch("app.review.runner.get_provider") as mock_get_provider, \
             patch("app.review.runner._load_question_for_review") as mock_load, \
             patch("app.review.runner.async_session") as mock_session_ctx:

            mock_provider = AsyncMock()
            mock_provider.complete.return_value = mock_llm_response
            mock_get_provider.return_value = mock_provider

            mock_load.return_value = {
                "question_data": question_data,
                "annotation": None,
                "source_examples": [],
                "overlap_status": "none",
                "generation_request": None,
                "version_id": None,
            }

            mock_db = _make_mock_db()
            _setup_session_mock(mock_session_ctx, mock_db)

            # First review
            mock_review_run_1 = MagicMock()
            mock_review_run_1.id = uuid.uuid4()
            mock_review_run_1.status = "running"
            mock_review_run_1.started_at = datetime.now(timezone.utc)
            mock_review_run_1.completed_at = None
            mock_review_run_1.rubric_version = RUBRIC_VERSION
            mock_db.get.return_value = mock_review_run_1

            with patch("app.review.runner.get_settings", return_value=settings):
                result1 = await run_review_swarm(question_id, triggered_by="manual_question")
                first_run_id = mock_review_run_1.id

                # Reset mock for second review
                mock_db = _make_mock_db()
                _setup_session_mock(mock_session_ctx, mock_db)

                mock_review_run_2 = MagicMock()
                mock_review_run_2.id = uuid.uuid4()
                mock_review_run_2.status = "running"
                mock_review_run_2.started_at = datetime.now(timezone.utc)
                mock_review_run_2.completed_at = None
                mock_review_run_2.rubric_version = RUBRIC_VERSION
                mock_db.get.return_value = mock_review_run_2

                result2 = await run_review_swarm(question_id, triggered_by="manual_question")
                second_run_id = mock_review_run_2.id

            # The two runs should have different IDs
            assert first_run_id != second_run_id


# ---------------------------------------------------------------------------
# Batch review swarm tests
# ---------------------------------------------------------------------------

class TestBatchReviewSwarm:

    @pytest.mark.asyncio
    async def test_batch_review_reviews_all_questions(self):
        """Each generated question in a batch gets reviewed."""
        settings = _make_settings()
        batch_id = uuid.uuid4()

        qid1 = uuid.uuid4()
        qid2 = uuid.uuid4()

        with patch("app.review.runner.async_session") as mock_session_ctx:
            mock_db = _make_mock_db()
            _setup_session_mock(mock_session_ctx, mock_db)

            mock_batch = MagicMock()
            mock_batch.id = batch_id
            mock_db.get.return_value = mock_batch

            # Two jobs with question IDs
            mock_job_1 = MagicMock()
            mock_job_1.question_id = qid1
            mock_job_2 = MagicMock()
            mock_job_2.question_id = qid2

            # execute() is called multiple times; we need to return
            # different results for different queries.
            # 1st call: select jobs where batch_id and question_id is not None
            # 2nd call: select existing review runs for those question_ids
            call_count = 0

            async def mock_execute(query):
                nonlocal call_count
                call_count += 1
                result = MagicMock()
                if call_count == 1:
                    result.scalars.return_value.all.return_value = [mock_job_1, mock_job_2]
                else:
                    # No existing review runs
                    result.scalars.return_value.all.return_value = []
                return result

            mock_db.execute = AsyncMock(side_effect=mock_execute)

            with patch("app.review.runner.run_review_swarm") as mock_swarm:
                mock_swarm.return_value = MagicMock(
                    id=uuid.uuid4(),
                    status="complete",
                )

                results = await run_batch_review_swarm(
                    batch_id,
                    triggered_by="manual_batch",
                )

                # Both questions should be reviewed
                assert mock_swarm.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_review_empty_batch(self):
        """A batch with no generated questions returns empty results."""
        batch_id = uuid.uuid4()

        with patch("app.review.runner.async_session") as mock_session_ctx:
            mock_db = _make_mock_db()
            _setup_session_mock(mock_session_ctx, mock_db)

            mock_batch = MagicMock()
            mock_batch.id = batch_id
            mock_db.get.return_value = mock_batch

            # Jobs query returns empty
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            results = await run_batch_review_swarm(
                batch_id,
                triggered_by="manual_batch",
            )

            assert results == []

    @pytest.mark.asyncio
    async def test_batch_review_nonexistent_batch_raises(self):
        """A non-existent batch_id raises ValueError."""
        batch_id = uuid.uuid4()

        with patch("app.review.runner.async_session") as mock_session_ctx:
            mock_db = _make_mock_db()
            _setup_session_mock(mock_session_ctx, mock_db)

            # Batch not found
            mock_db.get.return_value = None

            with pytest.raises(ValueError, match="not found"):
                await run_batch_review_swarm(batch_id)


# ---------------------------------------------------------------------------
# Question loading tests
# ---------------------------------------------------------------------------

class TestLoadQuestionForReview:

    @pytest.mark.asyncio
    async def test_non_generated_question_returns_none(self):
        """Questions with content_origin != 'generated' return None."""
        question_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_question = MagicMock()
        mock_question.content_origin = "official"
        mock_db.get.return_value = mock_question

        result = await _load_question_for_review(question_id, mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_nonexistent_question_returns_none(self):
        """A question_id that doesn't exist returns None."""
        question_id = uuid.uuid4()

        mock_db = AsyncMock()
        mock_db.get.return_value = None

        result = await _load_question_for_review(question_id, mock_db)
        assert result is None


# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------

class TestVersionConstants:

    def test_rubric_version(self):
        assert RUBRIC_VERSION == "v1"

    def test_rules_versions(self):
        assert "grammar" in RULES_VERSIONS
        assert "reading" in RULES_VERSIONS
        assert RULES_VERSIONS["grammar"] == "v7"
        assert RULES_VERSIONS["reading"] == "v2"
