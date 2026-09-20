# DOMAINS_SKILLS — Sep 2026 CB Verbal Bank

Unique domain × skill combinations as they appear on the test, deduplicated across the three difficulty PDFs (`EASY`, `MED`, `HARD`). 10 unique combinations total — all possible pairs, none missing from any tier.

| Domain | Skill |
|---|---|
| Craft and Structure | Cross-Text Connections |
| Craft and Structure | Text Structure and Purpose |
| Craft and Structure | Words in Context |
| Expression of Ideas | Rhetorical Synthesis |
| Expression of Ideas | Transitions |
| Information and Ideas | Central Ideas and Details |
| Information and Ideas | Command of Evidence |
| Information and Ideas | Inferences |
| Standard English Conventions | Boundaries |
| Standard English Conventions | Form, Structure, and Sense |

*Each skill appears with exactly one domain — no cross-domain combinations. Raw label count is 11: a `Cross-text Connections` casing variant occurs 3 times (once each in MED, HARD, and `MyPractice - Question Bank - Results11.pdf`) against 61 correct `Cross-Text Connections`, normalized above.*

*Verified 2026-09-20 against all nine verbal PDFs (4,465 label rows, 1,845 unique question IDs): zero conflicting Domain, Skill, Difficulty, or Correct Answer values across repeated IDs; zero blanks. `EASY ∪ MED ∪ HARD` partitions the 1,845 exactly, with no overlap. Re-run with `CB_QUESTION_BANK/09_2026/audit_cb.py` + `dedup.py`. Question counts per pair and the full audit are in [`ONTOLOGY_REFACTOR_PLAN.md`](ONTOLOGY_REFACTOR_PLAN.md).*