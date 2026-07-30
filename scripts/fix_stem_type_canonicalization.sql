-- bug-812: One-time canonicalization of stem_type_key across questions + annotations.
--
-- Principle (cerebrum Do-Not-Repeat 2026-07-29): annotation_jsonb is canonical/
-- authoritative; questions.stem_type_key is a denormalized copy that drifts.
-- Both storage locations are read:
--   - diagnostic blueprint filters on annotation_jsonb.stem_type_key (queries.py)
--   - practice recall + review facets read the questions.stem_type_key column
-- So column and jsonb must agree and both be canonical.
--
-- Repair buckets (active questions only):
--   940  jsonb canonical, column differs      -> align column <- jsonb
--    13  jsonb holds a stray value           -> alias-map column AND jsonb
--     1  jsonb lacks stem_type_key entirely   -> alias-map column, add key to jsonb
--     1  no annotation row at all             -> alias-map column only
--
-- Alias map is same-dimension task->task (the sanctioned _STEM_ALIASES mechanism
-- in extract_prompt.py), validated against the canonical stem phrasings:
--   "conforms to the conventions of standard English" -> conform_to_standard_english
--   "completes the text with the most logical transition" -> choose_best_transition
--   "The student wants to ..." notes synthesis -> choose_best_notes_synthesis
--
-- Pre-repair backup: backups/stem_type_pre_repair_<ts>.dump

BEGIN;

CREATE TEMP TABLE _stem_canon(k text) ON COMMIT DROP;
INSERT INTO _stem_canon VALUES
  ('complete_the_text'),('choose_main_idea'),('choose_main_purpose'),('choose_structure_description'),
  ('choose_sentence_function'),('choose_likely_response'),('choose_best_support'),('choose_best_quote'),
  ('choose_best_completion_from_data'),('choose_best_grammar_revision'),('choose_best_transition'),
  ('choose_best_notes_synthesis'),('choose_words_in_context'),('choose_word_in_context'),
  ('choose_cross_text_connection'),('choose_text_relationship'),('choose_agreement_across_texts'),
  ('choose_difference_across_texts'),('choose_best_inference'),('choose_command_of_evidence_textual'),
  ('choose_command_of_evidence_quantitative'),('choose_central_detail'),('choose_detail'),
  ('choose_best_illustration'),('choose_best_weakener'),('conform_to_standard_english'),
  ('most_logically_completes'),('synthesize_information'),('compare_contributions');

-- Same-dimension alias map (mirrors _STEM_ALIASES additions in extract_prompt.py).
CREATE TEMP TABLE _stem_alias(val text, canon text) ON COMMIT DROP;
INSERT INTO _stem_alias VALUES
  ('choose_grammatically_correct_form','conform_to_standard_english'),
  ('conventions_of_english','conform_to_standard_english'),
  ('grammar_convention','conform_to_standard_english'),
  ('choose_logical_transition','choose_best_transition'),
  ('synthesize_information_from_notes','choose_best_notes_synthesis'),
  ('synthesize_notes','choose_best_notes_synthesis');

-- ---- Step 1: align column <- jsonb wherever jsonb is canonical and they differ
UPDATE questions q
SET stem_type_key = a.annotation_jsonb->>'stem_type_key', updated_at = NOW()
FROM question_annotations a
WHERE q.latest_annotation_id = a.id
  AND q.practice_status = 'active'
  AND (a.annotation_jsonb->>'stem_type_key') IN (SELECT k FROM _stem_canon)
  AND q.stem_type_key IS DISTINCT FROM (a.annotation_jsonb->>'stem_type_key');

-- ---- Step 2a: canonicalize COLUMN for rows whose column still holds a stray alias value
--     (edge rows not aligned in step 1 because jsonb was stray/absent)
UPDATE questions q
SET stem_type_key = al.canon, updated_at = NOW()
FROM _stem_alias al
WHERE q.practice_status = 'active'
  AND q.stem_type_key = al.val;

-- ---- Step 2b: canonicalize JSONB for rows whose jsonb holds a stray alias value
UPDATE question_annotations a
SET annotation_jsonb = jsonb_set(annotation_jsonb, '{stem_type_key}', to_jsonb(al.canon::text))
FROM _stem_alias al
WHERE (a.annotation_jsonb->>'stem_type_key') = al.val;

-- ---- Step 2c: add stem_type_key into the 1 annotation jsonb that lacks the key
--     (its question column was synthesize_notes -> choose_best_notes_synthesis in 2a)
UPDATE question_annotations a
SET annotation_jsonb = jsonb_set(annotation_jsonb, '{stem_type_key}', to_jsonb('choose_best_notes_synthesis'::text))
FROM questions q
WHERE q.latest_annotation_id = a.id
  AND q.practice_status = 'active'
  AND q.stem_type_key = 'choose_best_notes_synthesis'
  AND (a.annotation_jsonb ? 'stem_type_key') = false;

-- ---- Verify: all three must be 0 before COMMIT
SELECT 'col_strays_remaining' AS check, count(*) AS n
FROM questions WHERE practice_status='active' AND stem_type_key IS NOT NULL
  AND stem_type_key NOT IN (SELECT k FROM _stem_canon)
UNION ALL
SELECT 'jsonb_strays_remaining', count(*)
FROM question_annotations a JOIN questions q ON q.latest_annotation_id=a.id
WHERE q.practice_status='active'
  AND (a.annotation_jsonb->>'stem_type_key') IS NOT NULL
  AND (a.annotation_jsonb->>'stem_type_key') NOT IN (SELECT k FROM _stem_canon)
UNION ALL
SELECT 'col_jsonb_disagree', count(*)
FROM questions q JOIN question_annotations a ON q.latest_annotation_id=a.id
WHERE q.practice_status='active'
  AND q.stem_type_key IS NOT NULL
  AND (a.annotation_jsonb->>'stem_type_key') IS NOT NULL
  AND q.stem_type_key <> (a.annotation_jsonb->>'stem_type_key');

-- COMMIT manually after verifying the three counts are all 0.
COMMIT;