# TODOS

## Harden stimulus detection (matcher + layout prompt)

**What:** Improve `match_stimulus_regions_for_question` heuristics and the
`detect_layout` prompt so fewer chart/table/figure stimuli fail to attach to a
question in the first place.

**Why:** `TASKS_OCR_IMAGE.md` builds a backfill workflow that *recovers* failed
stimuli but does not *reduce* failures. Two of the three failure classes trace
straight to detection quality: Class B (region never detected by
`detect_layout`) and Class C (region detected but `match_stimulus_regions_for_
question` attached it to no question). Recovering a failure is more expensive
than not producing it.

**Pros:** Fewer sentinel rows, fewer `needs_review` jobs, less backfill work,
less paid re-OCR spend. Prevention scales better than recovery.

**Cons:** Layout/matcher tuning is empirical and fiddly; risk of over-tightening
(false negatives) or over-loosening (false positives). No quick win guaranteed.

**Context:** Matcher heuristics live in `backend/app/storage/crop_detector.py`
(`match_stimulus_regions_for_question`, spatial thresholds `near_below`,
`near_above`, center-alignment). The layout prompt is
`backend/app/prompts/layout_prompt.py`. Best sequenced *after* Phase 1 of the
OCR backfill plan ships — the flag-scan report shows which class (A/B/C)
dominates, which tells you whether to invest in the matcher, the layout prompt,
or the vision model.

**Depends on / blocked by:** `TASKS_OCR_IMAGE.md` Phase 1 (flag-scan data to
prioritize the fix).
