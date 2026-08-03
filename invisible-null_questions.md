# Invisible NULL-Stimulus Questions

Questions with `stimulus_mode_key = NULL` (in both `questions.stimulus_mode_key` and `annotation_jsonb`), making them invisible in the **Pick a Concept → By Type** picker and unreachable via `stimulus_mode_key` filtering in Mixed Practice.

All 6 are `stem_type_key = synthesize_information` ("Choose Best Notes Synthesis") — the stimulus is bullet notes, so each belongs in the **Notes & Bullets** (`notes_bullets`) bucket and should be backfilled. See `bug-818` in `.wolf/buglog.json`.

Report generated: 2026-07-30 · Branch: `missed_question` · Source: live `dsat_dev` DB

## Summary

| Count | Status | Should be tagged |
|---|---|---|
| 5 | active (invisible to students) | `notes_bullets` |
| 1 | rejected | `notes_bullets` |

## Invisible questions

| # | Year | Test | Mod | Q# | Status | Notes stimulus |
|---|---|---|---|---|---|---|
| 1 | 2024 | Bluebook Practice Test 10 | 02A | 27 | active | Gullah / Cohen & Rodrigues — emphasize duration and purpose |
| 2 | 2024 | Test 7 | 02A | 26 | active | Royal Alcázar tiles — contrast two styles |
| 3 | 2024 | Test 7 | 02B | 27 | active | Solvay Conference — place Einstein's argument in historical context |
| 4 | 2024 | Test 5 | 02B | 26 | **rejected** | Elizabeth Catlett — (rejected, not served) |
| 5 | 2025 | Test 5 | 02 | 31 | active | Sirius A — emphasize mass |
| 6 | 2025 | Test 5 | 02 | 32 | active | Levers — contrast first-class vs second-class |

## Detail (with DB IDs)

### 1. Bluebook Practice Test 10 — Mod 02A — Q27 (active)
- **ID:** `e1149dae-d58c-5911-ab3c-b73595d49314`
- **Year:** 2024 · **Exam:** 10 · **Subject:** verbal · **Section:** 01 · **Module:** 02A · **Q#:** 27
- **Passage:** "While researching a topic, a student has taken the following notes: • The Gullah are a gr…"
- **Task:** "The student wants to emphasize the duration and purpose of Cohen's and Rodrigues's work…"

### 2. Test 7 — Mod 02A — Q26 (active)
- **ID:** `3b1b5db1-b859-5460-a12b-68f0000aa047`
- **Year:** 2024 · **Exam:** 07 · **Subject:** verbal · **Section:** 01 · **Module:** 02A · **Q#:** 26
- **source_test_name:** *(empty in DB)*
- **Passage:** "While researching a topic, a student has taken the following notes: * The Royal Alcázar o…"
- **Task:** "The student wants to contrast the two styles of tiles…"

### 3. Test 7 — Mod 02B — Q27 (active)
- **ID:** `34c3c246-fc81-5709-84c8-d82863795709`
- **Year:** 2024 · **Exam:** 07 · **Subject:** verbal · **Section:** 01 · **Module:** 02B · **Q#:** 27
- **source_test_name:** *(empty in DB)*
- **Passage:** "While researching a topic, a student has taken the following notes: * The fifth Solvay Co…"
- **Task:** "The student wants to place Einstein's argument within its historical context…"

### 4. Test 5 — Mod 02B — Q26 (REJECTED — not served)
- **ID:** `921d8e56-a051-5113-b003-c13cb37af050`
- **Year:** 2024 · **Exam:** 05 · **Subject:** verbal · **Section:** 01 · **Module:** 02B · **Q#:** 26
- **source_test_name:** *(empty in DB)*
- **Passage:** "While researching a topic, a student has taken the following notes: • Elizabeth Catlett's…"
- **Task:** "Which choice most effectively uses relevant information from the notes to accomplish this…"
- **Note:** `practice_status = rejected` — not served to students regardless, but should still be tagged for consistency.

### 5. Test 5 — Mod 02 — Q31 (active)
- **ID:** `986b4f2d-7ac5-5ed5-ab0a-73e6f783ca3b`
- **Year:** 2025 · **Test name:** Test_5_digital_sec01_mod02 · **Exam:** 5 · **Subject:** verbal · **Section:** 01 · **Module:** 02 · **Q#:** 31
- **Passage:** "While researching a topic, a student has taken the following notes: • In astronomy, the m…"
- **Task:** "The student wants to emphasize the mass of Sirius A…"

### 6. Test 5 — Mod 02 — Q32 (active)
- **ID:** `579482d0-e947-54b2-9f1c-d0017b6bfb42`
- **Year:** 2025 · **Test name:** Test_5_digital_sec01_mod02 · **Exam:** 5 · **Subject:** verbal · **Section:** 01 · **Module:** 02 · **Q#:** 32
- **Passage:** "While researching a topic, a student has taken the following notes: • A lever is a simple…"
- **Task:** "The student wants to contrast first-class levers and second-class levers…"

## Data-quality notes

- Rows 2–4 have an empty `source_test_name` column (only `source_exam_code` is populated). Worth backfilling the test name alongside the stimulus tag.
- All 6 are official (`content_origin = official`) and all use the "While researching a topic, a student has taken the following notes" stem pattern → stimulus form is bullet notes → canonical tag is `notes_bullets`.

## Recommended fix (bug-818)

Backfill all 6 rows to `stimulus_mode_key = 'notes_bullets'`, updating both the column and `annotation_jsonb->stimulus_mode_key`:

```sql
UPDATE question_annotations a
SET annotation_jsonb = jsonb_set(a.annotation_jsonb, '{stimulus_mode_key}', '"notes_bullets"')
FROM questions q
WHERE a.id = q.latest_annotation_id
  AND q.stem_type_key = 'synthesize_information'
  AND q.stimulus_mode_key IS NULL;

UPDATE questions
SET stimulus_mode_key = 'notes_bullets'
WHERE stem_type_key = 'synthesize_information' AND stimulus_mode_key IS NULL;
```

After this, all 5 active questions appear under **Notes & Bullets** (currently 128) in the By-Type picker.