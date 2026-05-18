-- dev_reset_ingestion.sql
-- DEV-ONLY: wipes all ingested question content so PDFs can be re-ingested
-- from scratch (clears the duplicate-checksum guard in question_assets).
--
-- KEEPS: users.
-- CLEARS: every question_* table, llm_evaluations, and (via CASCADE)
--         user_progress, since user_progress.question_id references questions.
--
-- TRUNCATE ... CASCADE resolves the circular self-FKs on `questions`
-- (canonical_official_question_id / derived_from_question_id) automatically.
-- RESTART IDENTITY resets serial sequences.
--
-- Run inside a transaction; rolls back entirely if anything fails.

BEGIN;

\echo 'Row counts BEFORE reset:'
SELECT 'question_jobs'           AS table, count(*) FROM question_jobs
UNION ALL SELECT 'questions',              count(*) FROM questions
UNION ALL SELECT 'question_versions',      count(*) FROM question_versions
UNION ALL SELECT 'question_annotations',   count(*) FROM question_annotations
UNION ALL SELECT 'question_options',       count(*) FROM question_options
UNION ALL SELECT 'question_assets',        count(*) FROM question_assets
UNION ALL SELECT 'llm_evaluations',        count(*) FROM llm_evaluations
UNION ALL SELECT 'user_progress',          count(*) FROM user_progress
UNION ALL SELECT 'users (kept)',           count(*) FROM users;

TRUNCATE
    question_jobs,
    question_job_questions,
    questions,
    question_versions,
    question_annotations,
    question_options,
    question_assets,
    question_source_spans,
    question_stimulus_assets,
    question_relations,
    llm_evaluations
RESTART IDENTITY CASCADE;

\echo 'Row counts AFTER reset:'
SELECT 'question_jobs'           AS table, count(*) FROM question_jobs
UNION ALL SELECT 'questions',              count(*) FROM questions
UNION ALL SELECT 'question_versions',      count(*) FROM question_versions
UNION ALL SELECT 'question_annotations',   count(*) FROM question_annotations
UNION ALL SELECT 'question_options',       count(*) FROM question_options
UNION ALL SELECT 'question_assets',        count(*) FROM question_assets
UNION ALL SELECT 'llm_evaluations',        count(*) FROM llm_evaluations
UNION ALL SELECT 'user_progress',          count(*) FROM user_progress
UNION ALL SELECT 'users (kept)',           count(*) FROM users;

COMMIT;

\echo 'Ingestion data cleared. PDFs can now be re-ingested.'
