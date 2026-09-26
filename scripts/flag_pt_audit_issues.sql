-- Source/PT audit, 2026-09-25: flag questions for admin review in question_issues.
-- Nothing is changed or rejected here; each row shows up under "Has open issues" in
-- Data Management. Idempotent: skips a (question, issue_type) already flagged by this audit.
-- Needs migrations 038 (question_issues) and 039 (source_pt_number).
-- Run: docker exec -i dsat-db psql -U dsat -d dsat_dev -v ON_ERROR_STOP=1 < scripts/flag_pt_audit_issues.sql
BEGIN;

CREATE TEMP TABLE audit_flags (question_id uuid, issue_type text, note text) ON COMMIT DROP;

CREATE TEMP VIEW audit_q AS
SELECT id, source_release_year yr, source_pt_number pt, source_section_code sec,
       upper(source_module_code) mod, source_question_number qn,
       concat_ws(' · ', source_release_year, 'PT' || lpad(source_pt_number::text, 2, '0'),
                 'Sec' || source_section_code, 'Mod' || source_module_code, 'Q' || source_question_number) label,
       md5(regexp_replace(lower(current_question_text || coalesce(current_passage_text, '')), '\s+', '', 'g')) h
FROM questions
WHERE content_origin = 'official' AND practice_status = 'active' AND source_pt_number IS NOT NULL;

-- 1. Same text, active more than once in the same test.
INSERT INTO audit_flags
SELECT a.id, 'duplicate',
       'Same question text is active more than once in this test: also '
       || string_agg(b.label || ' (' || left(b.id::text, 8) || ')', ', ' ORDER BY b.label)
       || '. Keep one and reject the others (keep the one with student answers or admin edits).'
FROM audit_q a JOIN audit_q b ON b.yr = a.yr AND b.pt = a.pt AND b.h = a.h AND b.id <> a.id
GROUP BY a.id;

-- 2. Two different active questions claim the same test slot.
INSERT INTO audit_flags
SELECT a.id, 'duplicate',
       'Another active question claims the same slot ' || a.label || ': '
       || string_agg(left(b.id::text, 8), ', ') || '. One of them is probably mislabelled.'
FROM audit_q a JOIN audit_q b
  ON b.yr = a.yr AND b.pt = a.pt AND b.sec = a.sec AND b.mod = a.mod AND b.qn = a.qn AND b.id <> a.id AND b.h <> a.h
GROUP BY a.id, a.label;

-- 3. 2024 PT4 rows stored as module 02, ingested from the Mod02B PDF.
INSERT INTO audit_flags
SELECT DISTINCT q.id, 'wrong_source_info',
       'Module is stored as 02, but this question was ingested from Test04_ENG_Sec01_Mod02B.pdf, so it is probably 02B.'
FROM questions q
JOIN question_job_questions qjq ON qjq.question_id = q.id
JOIN question_jobs qj ON qj.id = qjq.job_id
JOIN question_assets qa ON qa.id = qj.raw_asset_id
WHERE q.source_release_year = 2024 AND q.source_pt_number = 4 AND q.source_module_code = '02'
  AND qa.source_name = 'Test04_ENG_Sec01_Mod02B.pdf';

-- 4. 2024 PT2 rows stored as module 02 (exam code SAT): not a real module for this test.
INSERT INTO audit_flags
SELECT id, 'wrong_source_info',
       'Module is stored as 02, which is not a module of this test (01, 02A, 02B). Most rows in this set match PT2 02A text.'
FROM questions
WHERE content_origin = 'official' AND source_release_year = 2024 AND source_pt_number = 2 AND source_module_code = '02';

-- 5. 2025 "PT3" rows (retired) that are not in the Test 3 PDF; checked against the 2025 PDFs.
INSERT INTO audit_flags
SELECT v.id, 'wrong_source_info', v.note
FROM (VALUES
('ab9579af-fb24-5a8a-91d7-93e94146b415'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 4 mod02.'),
('b66852bb-a86f-55a1-bbbf-393dbcf2ebb4'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('3c1a2eeb-d76e-5498-9d9c-f7d843a60913'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('a8ccf897-d78e-5d82-8c52-95bf68b58567'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 1 mod01, Test 9 mod01.'),
('2238ed1a-5da0-50d6-8d20-bf0a051060d0'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 4 mod01.'),
('d0aebd83-67e7-5f4a-9409-cd7b8a2197fb'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 1 mod02.'),
('3537f56b-02c8-51ab-b2e4-7061b9f1086b'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('82996e32-9c3d-55cc-80ce-7a5ae7237538'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 9 mod02.'),
('02644076-6864-5b38-a590-0ebe267e42a0'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('fb86fcc5-2e0e-59d8-9a5c-dce45c4e67bf'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 9 mod01.'),
('b0fb9b26-3133-52dc-a503-75d8ca90e907'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 1 mod02, Test 10 mod01.'),
('8bdb79c8-a8d5-54b3-8291-f781ebb4e389'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('b4d8b52d-b338-5d0c-994d-11e7cd639e23'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('793ee075-de0c-5a54-b860-1d92b59e1407'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 4 mod02.'),
('08fa31db-71c3-54ea-b415-d3efdef1140f'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 9 mod01.'),
('1e111cd0-d942-5fce-a59e-4915e7ff6cab'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('fc8f6d34-2097-53c2-8c5a-0a3c28345261'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 4 mod01.'),
('4eb30a89-4ad1-5b11-8355-3bba0f38a1c6'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 9 mod02.'),
('f68a3151-bfcc-57b0-a4be-7a9077ef1d58'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 4 mod01.'),
('07cb9562-ad07-50ed-97fc-f504ec472070'::uuid, 'Labelled 2025 PT3, but its text is not in Test_3_digital_sec01_mod01.pdf or any other 2025 test PDF.'),
('54671d6c-0d07-504d-8a66-4434f49c632b'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it matches boilerplate found in most 2025 PDFs, so the source is unclear.'),
('42fcfaa2-b8e3-5fb2-bb48-aa5d56e3e31b'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 10 mod02.'),
('b0f2b550-1712-59b5-84d2-ee2f81585b52'::uuid, 'Labelled 2025 PT3, but its text is not in the Test 3 PDF; it appears in Test 9 mod02.')
) AS v(id, note);

INSERT INTO question_issues (id, question_id, issue_type, note, status, reported_by_role, reported_by_admin_token, created_at)
SELECT gen_random_uuid(), f.question_id, f.issue_type, string_agg(f.note, E'\n' ORDER BY f.note), 'open', 'admin', 'audit:pt-2026-09-25', now()
FROM audit_flags f
WHERE NOT EXISTS (
    SELECT 1 FROM question_issues i
    WHERE i.question_id = f.question_id AND i.issue_type = f.issue_type AND i.reported_by_admin_token = 'audit:pt-2026-09-25'
)
GROUP BY f.question_id, f.issue_type;

SELECT issue_type, count(*) AS flagged FROM question_issues
WHERE reported_by_admin_token = 'audit:pt-2026-09-25' GROUP BY 1 ORDER BY 1;

COMMIT;
