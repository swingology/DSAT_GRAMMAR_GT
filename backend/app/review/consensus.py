"""Consensus gate — deterministic verdict from review-swarm scores.

Phase 5 of TASKS_GENERATION. Converts per-reviewer scores and verdicts
into a single admin-facing consensus verdict using ordered first-match-wins
logic and config thresholds.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.db import ConsensusVerdict, LlmReviewResult, ReviewRun, Question

logger = logging.getLogger(__name__)


# --- Score keys that participate in averaging ---
_AVERAGE_DIMENSIONS = (
    "realism_score",
    "sat_fidelity_score",
    "difficulty_match_score",
    "distractor_quality_score",
    "taxonomy_match_score",
)

# Threshold keys in Settings (all floats, 0–10 scale)
_THRESHOLD_SETTINGS = {
    "realism_score": "generation_min_realism_score",
    "sat_fidelity_score": "generation_min_sat_fidelity_score",
    "distractor_quality_score": "generation_min_distractor_quality_score",
    "taxonomy_match_score": "generation_min_taxonomy_match_score",
}

# Inverted: higher is worse
_MAX_THRESHOLD_SETTINGS = {
    "copy_risk_score": "generation_max_copy_risk_score",
}

_DISAGREEMENT_SETTING = "generation_max_reviewer_disagreement"


def compute_consensus(
    review_results: Sequence[LlmReviewResult],
    *,
    overlap_status: str = "none",
) -> dict:
    """Compute a deterministic consensus verdict from review results.

    Returns a dict with all ConsensusVerdict column values (except id,
    question_id, review_run_id, generation_batch_id, created_at which are
    set by the caller).

    The verdict algorithm is ordered first-match-wins:

    1. blocked_overlap — question has unresolved official overlap
    2. insufficient_reviews — no successful reviewer results
    3. reject_recommended — any reviewer reports high copy risk
    4. reject_recommended — average realism below threshold
    5. admin_review_ready (with high_disagreement_flag) — reviewer
       disagreement exceeds threshold
    6. regenerate_recommended — any core dimension average below threshold
    7. admin_review_ready — all thresholds cleared
    """
    settings = get_settings()

    # Filter to successful reviews only
    ok_results = [r for r in review_results if r.review_status == "ok" and r.verdict is not None]

    reviewer_count = len(ok_results)
    reasons: list[str] = []

    # 1. Blocked overlap
    if overlap_status == "confirmed":
        return _verdict_dict(
            consensus_verdict="blocked_overlap",
            reviewer_count=reviewer_count,
            reasons=["Question has confirmed official overlap"],
            **_averages_and_votes(ok_results, reviewer_count),
        )

    if overlap_status == "possible":
        reasons.append("Question has possible official overlap (not yet resolved)")

    # 2. Insufficient reviews
    if reviewer_count == 0:
        return _verdict_dict(
            consensus_verdict="insufficient_reviews",
            reviewer_count=0,
            reasons=["No successful reviewer results"],
            **_zero_averages(),
        )

    # Compute averages from successful reviews
    avg = {}
    for dim in _AVERAGE_DIMENSIONS:
        values = [r.scores_jsonb.get(dim) for r in ok_results if isinstance(r.scores_jsonb, dict)]
        values = [v for v in values if isinstance(v, (int, float))]
        avg[dim] = sum(values) / len(values) if values else None

    copy_risk_values = [r.scores_jsonb.get("copy_risk_score") for r in ok_results if isinstance(r.scores_jsonb, dict)]
    copy_risk_values = [v for v in copy_risk_values if isinstance(v, (int, float))]
    max_copy_risk = max(copy_risk_values) if copy_risk_values else None

    # Vote counts
    accept_votes = sum(1 for r in ok_results if r.verdict == "accept")
    needs_review_votes = sum(1 for r in ok_results if r.verdict == "needs_human_review")
    reject_votes = sum(1 for r in ok_results if r.verdict == "reject")

    # 3. Reject recommended — high copy risk
    copy_risk_threshold = getattr(settings, _MAX_THRESHOLD_SETTINGS["copy_risk_score"])
    if max_copy_risk is not None and max_copy_risk > copy_risk_threshold:
        return _verdict_dict(
            consensus_verdict="reject_recommended",
            reviewer_count=reviewer_count,
            average_realism=avg.get("realism_score"),
            average_sat_fidelity=avg.get("sat_fidelity_score"),
            average_difficulty_match=avg.get("difficulty_match_score"),
            average_distractor_quality=avg.get("distractor_quality_score"),
            average_taxonomy_match=avg.get("taxonomy_match_score"),
            max_copy_risk=max_copy_risk,
            accept_votes=accept_votes,
            needs_review_votes=needs_review_votes,
            reject_votes=reject_votes,
            reasons=[f"Max copy risk {max_copy_risk:.1f} exceeds threshold {copy_risk_threshold}"],
        )

    # 4. Reject recommended — low realism
    realism_threshold = getattr(settings, _THRESHOLD_SETTINGS["realism_score"])
    if avg.get("realism_score") is not None and avg["realism_score"] < realism_threshold:
        return _verdict_dict(
            consensus_verdict="reject_recommended",
            reviewer_count=reviewer_count,
            average_realism=avg.get("realism_score"),
            average_sat_fidelity=avg.get("sat_fidelity_score"),
            average_difficulty_match=avg.get("difficulty_match_score"),
            average_distractor_quality=avg.get("distractor_quality_score"),
            average_taxonomy_match=avg.get("taxonomy_match_score"),
            max_copy_risk=max_copy_risk,
            accept_votes=accept_votes,
            needs_review_votes=needs_review_votes,
            reject_votes=reject_votes,
            reasons=[f"Average realism {avg['realism_score']:.1f} below threshold {realism_threshold}"],
        )

    # 5. Reviewer disagreement
    disagreement = _compute_disagreement(ok_results, avg)
    max_disagreement = getattr(settings, _DISAGREEMENT_SETTING)
    high_disagreement_flag = disagreement is not None and disagreement > max_disagreement

    if high_disagreement_flag:
        reasons.append(f"Reviewer disagreement {disagreement:.2f} exceeds threshold {max_disagreement}")

    # 6. Regenerate recommended — any core dimension below threshold
    below_threshold_dims = []
    for dim, setting_key in _THRESHOLD_SETTINGS.items():
        threshold = getattr(settings, setting_key)
        if avg.get(dim) is not None and avg[dim] < threshold:
            below_threshold_dims.append(f"{dim} {avg[dim]:.1f} < {threshold}")

    # Also check copy risk as an inverted dimension (already handled above for reject,
    # but for admin_review_ready we flag borderline copy risk)
    if max_copy_risk is not None and max_copy_risk > copy_risk_threshold * 0.8:
        reasons.append(f"Borderline copy risk: {max_copy_risk:.1f}")

    # Possible overlap flag
    if overlap_status == "possible":
        reasons.append("Possible overlap not yet resolved; admin should verify before approving")

    if below_threshold_dims and not high_disagreement_flag:
        return _verdict_dict(
            consensus_verdict="regenerate_recommended",
            reviewer_count=reviewer_count,
            average_realism=avg.get("realism_score"),
            average_sat_fidelity=avg.get("sat_fidelity_score"),
            average_difficulty_match=avg.get("difficulty_match_score"),
            average_distractor_quality=avg.get("distractor_quality_score"),
            average_taxonomy_match=avg.get("taxonomy_match_score"),
            max_copy_risk=max_copy_risk,
            accept_votes=accept_votes,
            needs_review_votes=needs_review_votes,
            reject_votes=reject_votes,
            reviewer_disagreement=disagreement,
            high_disagreement_flag=high_disagreement_flag,
            reasons=[f"Below threshold: {', '.join(below_threshold_dims)}"],
        )

    # 7. Admin review ready — all thresholds cleared
    return _verdict_dict(
        consensus_verdict="admin_review_ready",
        reviewer_count=reviewer_count,
        average_realism=avg.get("realism_score"),
        average_sat_fidelity=avg.get("sat_fidelity_score"),
        average_difficulty_match=avg.get("difficulty_match_score"),
        average_distractor_quality=avg.get("distractor_quality_score"),
        average_taxonomy_match=avg.get("taxonomy_match_score"),
        max_copy_risk=max_copy_risk,
        accept_votes=accept_votes,
        needs_review_votes=needs_review_votes,
        reject_votes=reject_votes,
        reviewer_disagreement=disagreement,
        high_disagreement_flag=high_disagreement_flag,
        reasons=reasons if reasons else None,
    )


def _compute_disagreement(
    ok_results: Sequence[LlmReviewResult],
    averages: dict,
) -> float | None:
    """Compute mean standard deviation across all scored dimensions.

    Returns the average of per-dimension standard deviations, or None
    if there are fewer than 2 reviewers.
    """
    if len(ok_results) < 2:
        return None

    dim_stds = []
    for dim in _AVERAGE_DIMENSIONS:
        values = [r.scores_jsonb.get(dim) for r in ok_results if isinstance(r.scores_jsonb, dict)]
        values = [v for v in values if isinstance(v, (int, float))]
        if len(values) < 2:
            continue
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        dim_stds.append(variance ** 0.5)

    # Also include copy_risk_score
    copy_values = [r.scores_jsonb.get("copy_risk_score") for r in ok_results if isinstance(r.scores_jsonb, dict)]
    copy_values = [v for v in copy_values if isinstance(v, (int, float))]
    if len(copy_values) >= 2:
        mean = sum(copy_values) / len(copy_values)
        variance = sum((v - mean) ** 2 for v in copy_values) / len(copy_values)
        dim_stds.append(variance ** 0.5)

    return sum(dim_stds) / len(dim_stds) if dim_stds else None


def _verdict_dict(
    *,
    consensus_verdict: str,
    reviewer_count: int,
    reasons: list[str] | None = None,
    average_realism: float | None = None,
    average_sat_fidelity: float | None = None,
    average_difficulty_match: float | None = None,
    average_distractor_quality: float | None = None,
    average_taxonomy_match: float | None = None,
    max_copy_risk: float | None = None,
    accept_votes: int = 0,
    needs_review_votes: int = 0,
    reject_votes: int = 0,
    reviewer_disagreement: float | None = None,
    high_disagreement_flag: bool = False,
) -> dict:
    """Build a dict matching ConsensusVerdict columns (minus id/FK/timestamps)."""
    return {
        "reviewer_count": reviewer_count,
        "average_realism": average_realism,
        "average_sat_fidelity": average_sat_fidelity,
        "average_difficulty_match": average_difficulty_match,
        "average_distractor_quality": average_distractor_quality,
        "average_taxonomy_match": average_taxonomy_match,
        "max_copy_risk": max_copy_risk,
        "accept_votes": accept_votes,
        "needs_review_votes": needs_review_votes,
        "reject_votes": reject_votes,
        "reviewer_disagreement": reviewer_disagreement,
        "high_disagreement_flag": high_disagreement_flag,
        "consensus_verdict": consensus_verdict,
        "reasons_jsonb": reasons or [],
    }


def _zero_averages() -> dict:
    """Return a verdict dict with all averages None and zero votes."""
    return {
        "average_realism": None,
        "average_sat_fidelity": None,
        "average_difficulty_match": None,
        "average_distractor_quality": None,
        "average_taxonomy_match": None,
        "max_copy_risk": None,
        "accept_votes": 0,
        "needs_review_votes": 0,
        "reject_votes": 0,
        "reviewer_disagreement": None,
        "high_disagreement_flag": False,
    }


def _averages_and_votes(
    ok_results: Sequence[LlmReviewResult],
    reviewer_count: int,
) -> dict:
    """Compute averages and votes for early-exit verdicts (blocked_overlap, etc.)."""
    if reviewer_count == 0:
        return _zero_averages()

    avg = {}
    for dim in _AVERAGE_DIMENSIONS:
        values = [r.scores_jsonb.get(dim) for r in ok_results if isinstance(r.scores_jsonb, dict)]
        values = [v for v in values if isinstance(v, (int, float))]
        avg[dim] = sum(values) / len(values) if values else None

    copy_values = [r.scores_jsonb.get("copy_risk_score") for r in ok_results if isinstance(r.scores_jsonb, dict)]
    copy_values = [v for v in copy_values if isinstance(v, (int, float))]
    max_copy_risk = max(copy_values) if copy_values else None

    return {
        "average_realism": avg.get("realism_score"),
        "average_sat_fidelity": avg.get("sat_fidelity_score"),
        "average_difficulty_match": avg.get("difficulty_match_score"),
        "average_distractor_quality": avg.get("distractor_quality_score"),
        "average_taxonomy_match": avg.get("taxonomy_match_score"),
        "max_copy_risk": max_copy_risk,
        "accept_votes": sum(1 for r in ok_results if r.verdict == "accept"),
        "needs_review_votes": sum(1 for r in ok_results if r.verdict == "needs_human_review"),
        "reject_votes": sum(1 for r in ok_results if r.verdict == "reject"),
        "reviewer_disagreement": None,
        "high_disagreement_flag": False,
    }


async def save_consensus(
    question_id: uuid.UUID,
    review_run_id: uuid.UUID,
    review_results: Sequence[LlmReviewResult],
    *,
    overlap_status: str = "none",
    generation_batch_id: uuid.UUID | None = None,
    db: AsyncSession,
) -> ConsensusVerdict:
    """Compute consensus and persist it. Returns the saved ConsensusVerdict."""
    consensus_data = compute_consensus(review_results, overlap_status=overlap_status)

    verdict = ConsensusVerdict(
        id=uuid.uuid4(),
        question_id=question_id,
        review_run_id=review_run_id,
        generation_batch_id=generation_batch_id,
        **consensus_data,
    )
    db.add(verdict)
    await db.commit()
    return verdict