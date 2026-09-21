# Annotations vs College Board — conflict report

Read-only. 1456 official questions carry College Board labels; each is compared with its latest annotation. **Nothing here has been changed.** Correcting an annotation is a rewrite, so it is the owner's decision. Row-level detail: `cb_annotation_conflicts.json`.

| Conflict | Rows | Active | Hand-edited |
|---|---|---|---|
| difficulty: difficulty_overall differs from College Board | 835 | 803 | 233 |
| domain: question_family_key differs from College Board | 162 | 157 | 71 |
| reading skill: skill_family_key missing | 111 | 107 | 46 |
| routing: a reading question carries a grammar_role_key (served as grammar) | 87 | 83 | 34 |
| domain: question_family_key missing | 46 | 46 | 9 |
| routing: a grammar question carries skill_family_key (served as reading) | 26 | 26 | 23 |
| reading skill: skill_family_key differs from College Board | 22 | 20 | 4 |

## domain: question_family_key differs from College Board

| annotation says | College Board says | rows |
|---|---|---|
| `expression_of_ideas` | `craft_and_structure` | 78 |
| `conventions_grammar` | `expression_of_ideas` | 37 |
| `information_and_ideas` | `expression_of_ideas` | 23 |
| `standard_english_conventions` | `conventions_grammar` | 9 |
| `information_and_ideas` | `craft_and_structure` | 9 |
| `craft_and_structure` | `information_and_ideas` | 3 |
| `expression_of_ideas` | `conventions_grammar` | 1 |
| `craft_and_structure` | `expression_of_ideas` | 1 |
| `conventions_grammar` | `craft_and_structure` | 1 |

## reading skill: skill_family_key differs from College Board

| annotation says | College Board says | rows |
|---|---|---|
| `inferences` | `central_ideas_and_details` | 8 |
| `central_ideas_and_details` | `text_structure_and_purpose` | 6 |
| `text_structure_and_purpose` | `central_ideas_and_details` | 3 |
| `central_ideas_and_details` | `inferences` | 2 |
| `command_of_evidence_textual` | `central_ideas_and_details` | 1 |
| `command_of_evidence_textual` | `text_structure_and_purpose` | 1 |
| `command_of_evidence_textual` | `inferences` | 1 |

## difficulty: difficulty_overall differs from College Board

| annotation says | College Board says | rows |
|---|---|---|
| `medium` | `hard` | 383 |
| `medium` | `easy` | 181 |
| `low` | `medium` | 177 |
| `low` | `hard` | 91 |
| `easy` | `easy` | 1 |
| `hard` | `hard` | 1 |
| `high` | `medium` | 1 |

## What acting on this would mean

- **Routing rows are live bugs**: those questions are served in the wrong practice pool today, because the app routes on which annotation key is present.
- `questions.skill_key` already holds College Board's skill for every row here, so a reader that uses `skill_key` is unaffected by the annotation errors.
- Overwriting `difficulty_overall` would change adaptive module selection and the diagnostic pool; `cb_difficulty` is available without touching it.

