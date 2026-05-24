# TRAPS_EXAMPLES.md

Real examples of grammar traps from official DSAT practice tests, with rule keys and distractor analysis.

---

## PT5 M2 Q21 — `subject_verb_agreement` + `long_distance_dependency`

**Source:** Test 5, Section 1, Module 2, Question 21
**Grammar role:** `agreement`
**Grammar focus:** `subject_verb_agreement`
**Secondary focus:** `verb_tense_consistency` (scientific general present)
**Syntactic trap:** `long_distance_dependency`
**Difficulty:** medium
**Correct answer:** D

---

### Stimulus

> Oyster mushrooms typically get their nutrients from the damp logs on which they grow, but the fungi are also carnivorous, with the ability to kill and consume microscopic worms known as nematodes. As researcher Yen-Ping Hsueh has shown, the mushrooms release a toxin that is deadly to nematodes that _____ in contact with it.

### Options

| Label | Text | Correct |
|-------|------|---------|
| A | has come | no |
| B | comes | no |
| C | is coming | no |
| D | come | yes |

---

### Grammar Keys

**Rule 1 — Subject-verb agreement in a relative clause**
The blank is the verb of the relative clause "that _____ in contact with it." The relative pronoun *that* refers back to **nematodes** (plural). The verb must therefore be plural.

**Rule 2 — Scientific general present**
The passage states biological facts throughout using simple present (*mushrooms get, fungi are, mushrooms release*). The blank must match: simple present, plural.

Only **come** (D) satisfies both rules.

---

### Option Analysis

| Choice | Number | Aspect | Error |
|--------|--------|--------|-------|
| A — has come | singular | present perfect | Wrong number; wrong aspect for a general biological fact |
| B — comes | singular | simple present | Wrong number (correct tense register — most tempting distractor) |
| C — is coming | singular | progressive | Wrong number; progressive implies temporary ongoing action, not a general truth |
| D — come | plural | simple present | ✅ Correct |

---

### Trap Mechanism

The sentence contains two stacked relative clauses:

> "a toxin **[that is deadly to nematodes]** **[that _____ in contact with it]**"

Students lose track of the second *that*'s antecedent. The nearest plausible subject before the blank is *toxin* (singular) or even *contact*, pulling toward singular verbs like *comes* (B) or *has come* (A). The true antecedent — **nematodes** — sits two clauses back.

**Student failure mode:** `nearest_noun_reflex` — anchoring to *toxin* (singular) instead of tracing *that* back to *nematodes* (plural).

---

### Generation Profile

```json
{
  "grammar_role_key": "agreement",
  "grammar_focus_key": "subject_verb_agreement",
  "secondary_grammar_focus_keys": ["verb_tense_consistency"],
  "syntactic_trap_key": "long_distance_dependency",
  "passage_tense_register_key": "scientific_general_present",
  "target_distractor_pattern": [
    "singular present perfect — wrong number and aspect (A)",
    "singular simple present — wrong number only, correct tense (B, tightest distractor)",
    "singular progressive — wrong number and aspect (C)"
  ]
}
```
