"""Parse and validate review swarm JSON output against the rubric schema."""

from app.parsers.json_parser import extract_json_from_text


REQUIRED_SCORE_KEYS = (
    "realism_score",
    "sat_fidelity_score",
    "difficulty_match_score",
    "distractor_quality_score",
    "taxonomy_match_score",
    "explanation_quality_score",
    "copy_risk_score",
)

VALID_VERDICTS = ("accept", "needs_human_review", "reject")

MIN_SCORE = 0.0
MAX_SCORE = 10.0


class ReviewParseError(ValueError):
    """Raised when review JSON is malformed or missing required fields."""


def parse_review_json(
    raw_text: str,
    *,
    provider_name: str = "",
    model_name: str = "",
) -> dict:
    """Extract and validate review JSON from LLM output.

    Returns a dict with:
      - scores_jsonb: dict of 7 dimension scores
      - verdict: str
      - review_notes: str or None
      - raw_response_jsonb: the full parsed JSON

    Raises ReviewParseError on missing/invalid fields.
    """
    parsed = extract_json_from_text(
        raw_text, provider_name=provider_name, model_name=model_name
    )

    # Validate required score keys
    scores = {}
    for key in REQUIRED_SCORE_KEYS:
        if key not in parsed:
            raise ReviewParseError(f"Missing required score key: {key}")
        value = parsed[key]
        if not isinstance(value, (int, float)):
            raise ReviewParseError(
                f"Score {key} must be numeric, got {type(value).__name__}"
            )
        if value < MIN_SCORE or value > MAX_SCORE:
            raise ReviewParseError(
                f"Score {key}={value} out of range [{MIN_SCORE}, {MAX_SCORE}]"
            )
        scores[key] = float(value)

    # Validate verdict
    verdict = parsed.get("verdict")
    if verdict not in VALID_VERDICTS:
        raise ReviewParseError(
            f"Invalid verdict: {verdict!r}. Must be one of {VALID_VERDICTS}"
        )

    # Extract optional reasons
    reasons = parsed.get("reasons", {})
    if reasons is not None and not isinstance(reasons, dict):
        raise ReviewParseError(
            f"'reasons' must be a dict, got {type(reasons).__name__}"
        )

    # Compose review_notes from reasons if present
    review_notes = None
    if reasons and isinstance(reasons, dict):
        parts = [f"{k}: {v}" for k, v in reasons.items() if isinstance(v, str)]
        if parts:
            review_notes = "; ".join(parts)

    return {
        "scores_jsonb": scores,
        "verdict": verdict,
        "review_notes": review_notes,
        "raw_response_jsonb": parsed,
    }


def validate_review_scores(scores_jsonb: dict) -> list[str]:
    """Return dimension names where the score is below its threshold.

    Uses the config threshold values from the locked decisions.
    This function is used by Phase 5 consensus logic.
    """
    from app.config import get_settings

    settings = get_settings()
    thresholds = {
        "realism_score": settings.generation_min_realism_score,
        "sat_fidelity_score": settings.generation_min_sat_fidelity_score,
        "distractor_quality_score": settings.generation_min_distractor_quality_score,
        "taxonomy_match_score": settings.generation_min_taxonomy_match_score,
    }
    # copy_risk is inverted: above threshold is bad
    copy_risk_threshold = settings.generation_max_copy_risk_score

    below = []
    for key, threshold in thresholds.items():
        if key in scores_jsonb and scores_jsonb[key] < threshold:
            below.append(key)
    if "copy_risk_score" in scores_jsonb and scores_jsonb["copy_risk_score"] > copy_risk_threshold:
        below.append("copy_risk_score")
    return below