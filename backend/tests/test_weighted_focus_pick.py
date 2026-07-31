"""Unit tests for the weakness-weighted focus key picker used by Mixed Practice."""

import random

from app.models.payload import WeaknessTarget
from app.routers.student import _weighted_focus_key_pick


def _target(focus_key: str, domain: str, score: float) -> WeaknessTarget:
    return WeaknessTarget(
        domain=domain,
        focus_key=focus_key,
        skill_family_key=None,
        grammar_role_key=None,
        difficulty="medium",
        weakness_score=score,
        miss_count=1,
        attempt_count=1,
        miss_rate=1.0,
        days_since_last_attempt=0.0,
        inventory_unseen=10,
        inventory_below_threshold=False,
    )


def test_returns_none_for_empty_targets():
    assert _weighted_focus_key_pick([]) is None


def test_returns_none_when_all_scores_are_zero():
    targets = [_target("comma_splice", "grammar", 0.0), _target("modifier", "grammar", 0.0)]
    assert _weighted_focus_key_pick(targets) is None


def test_single_target_is_always_picked():
    targets = [_target("comma_splice", "grammar", 0.8)]
    assert _weighted_focus_key_pick(targets) == ("grammar", "comma_splice")


def test_pick_is_one_of_the_input_targets():
    targets = [
        _target("comma_splice", "grammar", 0.9),
        _target("inference", "reading", 0.3),
    ]
    rng = random.Random(1234)
    result = _weighted_focus_key_pick(targets, rng=rng)
    assert result in {("grammar", "comma_splice"), ("reading", "inference")}


def test_higher_weight_is_picked_more_often_with_seeded_rng():
    targets = [
        _target("weak_concept", "grammar", 0.95),
        _target("strong_concept", "grammar", 0.01),
    ]
    rng = random.Random(42)
    picks = [_weighted_focus_key_pick(targets, rng=rng) for _ in range(200)]
    weak_count = sum(1 for p in picks if p == ("grammar", "weak_concept"))
    # With a 95:1 weight ratio, the heavy target should dominate but not be
    # guaranteed every time — asserts bias without asserting a hard-priority order.
    assert weak_count > 150
    assert weak_count < 200
