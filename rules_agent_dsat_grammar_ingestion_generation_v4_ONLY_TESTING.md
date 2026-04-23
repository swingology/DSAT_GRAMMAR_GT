# rules_agent_dsat_grammar_ingestion_generation_v4_ONLY_TESTING.md

## ONLY TESTING

This section is written for testing, validation, and psychometric realism only.

It defines:
- the seven methods for making distractors more irresistible
- the Module Composition Engine
- testing-only validation rules for module sequencing, fatigue, answer balance, and distractor competitiveness

This section is intended to be appended after V3.

---

## 30. Seven Ways to Make Wrong Answers More Irresistible

### 30.1 Core Principle

A strong SAT distractor is not attractive because it is bizarre or tricky.

It is attractive because it feels correct faster than the correct answer does.

The best distractor is the one a strong student picks confidently on first read and only later realizes is wrong under precise reasoning.

Each distractor should therefore be engineered not merely to be wrong, but to be psychologically tempting.

---

### 30.2 Method 1 — Reward the First Read

A distractor should appear correct on a quick surface reading.

It should survive the test-taker’s first-pass scan and fail only under more careful inspection.

#### Rule
At least one distractor in a high-quality item must pass a first-read plausibility test.

#### Example pattern
- correct answer = precise but plain
- distractor = slightly broader or more familiar synonym

#### Testing field
```json
{
  "first_read_plausibility": "high"
}
```

Allowed values:
- `low`
- `medium`
- `high`

Production target for at least one distractor: `high`

---

### 30.3 Method 2 — Exploit a Real Student Habit

A distractor should target a real student reflex, not an invented puzzle mechanism.

#### Approved student reflexes
- nearest noun agreement reflex
- comma equals pause equals correct
- longer answer sounds smarter
- formal word sounds better
- grammatically smooth must be correct
- first acceptable answer bias
- “this sounds more academic” bias
- timeline assumption bias
- extreme word over-selection
- modifier blindness

#### Rule
Every distractor must map to a documented failure habit.

#### Testing field
```json
{
  "student_failure_mode_key": "formal_word_bias"
}
```

This field is mandatory for all distractors.

---

### 30.4 Method 3 — Be Wrong for a Tiny Reason

The strongest distractors are almost correct.

They fail because of one narrow, decisive flaw:
- a logic mismatch
- a scope error
- a tense inconsistency
- a register misfit
- a precision failure
- an agreement break
- a wrong discourse relationship

#### Rule
At least one distractor must be wrong for a narrow precision reason rather than for an obvious grammar or logic failure.

#### Testing field
```json
{
  "fatal_flaw_size": "tiny"
}
```

Allowed values:
- `large`
- `medium`
- `tiny`

Preferred value for hardest distractor: `tiny`

---

### 30.5 Method 4 — Use Truth-Adjacent Answers

Some distractors should be broadly true, but not responsive to the exact question asked.

These distractors feel safe because they align with the topic, but they fail relevance, specificity, or evidence alignment.

#### Rule
For reading questions, at least one distractor may be factually or conceptually adjacent to the text while still failing the task.

#### Testing field
```json
{
  "truth_adjacent_distractor": true
}
```

Use only when the item type supports this naturally.

---

### 30.6 Method 5 — Hide the Error in the Least-Looked Place

Students often inspect only the most visible part of an answer.

The best distractors place the error in a low-attention zone:
- a modifier
- a scope word
- a tense shift
- a conjunction
- a pronoun reference
- a comparison target
- a limiting word such as `all`, `most`, `only`, or `primarily`

#### Rule
At least one distractor in medium or high difficulty items should place its fatal flaw in a low-attention zone.

#### Testing field
```json
{
  "error_visibility": "low"
}
```

Allowed values:
- `high`
- `medium`
- `low`

Production target for at least one distractor in hard items: `low`

---

### 30.7 Method 6 — Use Emotional Confidence Traps

Some distractors should feel more sophisticated, polished, or “academic” than the correct answer.

Students often overtrust answers that sound smarter.

Examples:
- more formal diction
- more ornate phrasing
- more abstract terminology
- more technical wording
- more polished rhythm

#### Rule
At least one distractor may exploit formal-word bias or sophistication bias when natural.

#### Testing field
```json
{
  "confidence_trap_type": "formal_word_bias"
}
```

Allowed values:
- `formal_word_bias`
- `longer_answer_bias`
- `polished_syntax_bias`
- `technicality_bias`
- `none`

---

### 30.8 Method 7 — Make the Correct Answer Slightly Less Sexy

The correct answer should often feel plainer, more direct, and less flashy than the best distractor.

This reflects official SAT style.

The correct answer should win because it is more precise, not because it sounds more impressive.

#### Rule
Do not systematically make the correct answer the longest, most sophisticated, or most rhetorically striking option.

#### Testing field
```json
{
  "correct_answer_flashiness": "low"
}
```

Allowed values:
- `low`
- `medium`
- `high`

Preferred value: `low` or `medium`

---

### 30.9 Distractor Irresistibility Composite Score

```json
{
  "distractor_irresistibility_score": 0.88
}
```

This score estimates how compelling the distractors are under realistic timed conditions.

#### Scale

| Score | Meaning |
|---|---|
| 0.20–0.45 | weak distractors |
| 0.45–0.65 | acceptable distractors |
| 0.65–0.80 | strong SAT-quality distractors |
| 0.80–0.92 | highly irresistible official-style distractors |
| 0.92+ | extremely strong distractors; use carefully to avoid unfairness |

Preferred production range: `0.80–0.90`

---

## 31. Module Composition Engine

### 31.1 Purpose

Official-feeling SAT realism is not only question-level.

It is module-level.

A module should feel intentionally composed:
- difficulty should ramp naturally
- item types should rotate
- answer positions should feel balanced
- fatigue pressure should increase in plausible ways
- late questions should not all behave the same way
- hard items should cluster realistically without becoming predictable

The Module Composition Engine governs those requirements.

---

### 31.2 Module Blueprint Object

```json
{
  "module_blueprint": {
    "module_length": 33,
    "opening_band": "easy_to_medium",
    "transition_band_start": 6,
    "hard_cluster_start": 18,
    "late_precision_cluster_start": 26,
    "fatigue_zone_start": 24
  }
}
```

This blueprint controls how difficulty and distractor competition vary across a full module.

---

### 31.3 Recommended Difficulty Flow

For a standard Reading and Writing module:

#### Questions 1–5
- easier to medium
- lower syntax density
- wider or moderate distractor distance
- quick solvability
- strong clarity

#### Questions 6–12
- medium
- tighter semantic distinctions
- increased inference load
- distractors become more competitive

#### Questions 13–20
- medium to high
- deeper structural reading
- more answer competition
- more precise elimination required

#### Questions 21–27
- high
- tight distractor distance preferred
- more low-visibility fatal flaws
- more fatigue-sensitive traps

#### Questions 28–33
- high but fair
- close precision discrimination
- stronger pressure on scope, structure, and wording
- avoid excessive ambiguity
- finish with legitimacy, not chaos

---

### 31.4 Difficulty Ramp Rules

```json
{
  "module_difficulty_ramp": "progressive"
}
```

Allowed values:
- `flat`
- `progressive`
- `clustered_progressive`

Preferred value: `clustered_progressive`

#### Meaning
- `flat`: little variation in difficulty; not realistic for official-feeling modules
- `progressive`: steady rise in difficulty
- `clustered_progressive`: difficulty rises overall, but hard items appear in realistic clusters

Preferred production behavior: `clustered_progressive`

---

### 31.5 Module Composition Targets by Region

| Region | Question Range | Primary goal |
|---|---|---|
| Opening | 1–5 | Establish rhythm and confidence |
| Transition | 6–12 | Increase interpretive and precision demand |
| Mid-module core | 13–20 | Rotate item types and increase competition |
| Hard cluster | 21–27 | Tight distractors, low separation strength |
| Fatigue zone | 28–33 | High precision demand under time pressure |

---

### 31.6 Item-Type Rotation Rules

A realistic module should not over-cluster one question family.

#### Rule
No more than 3 consecutive items may share the same `question_family_key` unless modeling a deliberate official-style cluster.

#### Testing field
```json
{
  "item_type_rotation_check": true
}
```

#### Additional rule
Within any 8-question window, include at least 3 distinct question families.

---

### 31.7 Answer Position Distribution Engine

Correct answers should not form obvious patterns.

#### Module-level answer position target
```json
{
  "answer_position_distribution": {
    "A": 8,
    "B": 9,
    "C": 8,
    "D": 8
  }
}
```

For a 33-question module, exact symmetry is not required, but visible imbalance is forbidden.

#### Rules
- no streak longer than 3 identical answer positions
- avoid obvious repeated cycles
- no answer letter should be underrepresented by more than 3 relative to another

#### Testing field
```json
{
  "recent_answer_bias_check": true
}
```

---

### 31.8 Option Length Symmetry

One of the most common AI tells is visual answer leakage.

#### Rule
The correct answer must not be identifiable by being consistently longer, shorter, or structurally more polished than the distractors.

#### Testing field
```json
{
  "option_length_balance_score": 0.91
}
```

Preferred minimum: `0.85`

---

### 31.9 Register Consistency Check

All four options in a given item must match in register, tone, and syntactic polish unless register mismatch is itself the tested skill.

#### Testing field
```json
{
  "register_consistency_score": 0.94
}
```

Preferred minimum: `0.90`

---

### 31.10 Fatigue Pressure Index

```json
{
  "fatigue_pressure_index": 0.81
}
```

This estimates how much time pressure and accumulated cognitive fatigue affect the likely success rate for the item in its module position.

#### Rule
Items later in the module may be slightly more punishing in distractor competition and precision demand, but not more ambiguous.

#### Scale
| Score | Meaning |
|---|---|
| 0.20–0.40 | low fatigue pressure |
| 0.40–0.65 | moderate fatigue pressure |
| 0.65–0.85 | realistic late-module pressure |
| 0.85+ | use carefully; risk of unfairness |

Preferred late-module range: `0.65–0.82`

---

### 31.11 Late-Fatigue Trap Rules

In late-module positions, the generator may increase:
- distractor distance tightness
- low-visibility error placement
- semantic similarity between options
- answer separation difficulty

But the generator must not increase:
- ambiguity
- dependence on outside knowledge
- artificial wording
- unresolvable competition

#### Rule
Late pressure should feel harder because it is more exacting, not because it is less fair.

---

### 31.12 Module-Level Distractor Balance

A module must distribute distractor mechanisms realistically.

#### Rule
Within a 33-question module:
- do not overuse one failure mode
- do not use the same trap mechanic in 3 consecutive grammar items
- rotate between semantic, structural, scope, register, and syntax-based traps

#### Testing field
```json
{
  "trap_variety_score": 0.89
}
```

Preferred minimum: `0.80`

---

### 31.13 Module-Level Quality Checklist

Before releasing a generated module, validate all of the following:

1. difficulty progression is plausible
2. answer distribution is balanced
3. item-type rotation is realistic
4. no visible answer streak patterns
5. hard cluster exists but is not overconcentrated
6. fatigue zone increases precision pressure without reducing fairness
7. option length symmetry is acceptable
8. register consistency is acceptable
9. trap variety is acceptable
10. no section of the module feels mechanically repetitive

#### Module release block
```json
{
  "module_release_ready": true
}
```

This must be `false` if any module-level composition check fails.

---

## 32. Testing-Only Enforcement Summary

The following testing-only fields are mandatory for V4 module validation:

```json
{
  "first_read_plausibility": "high",
  "fatal_flaw_size": "tiny",
  "truth_adjacent_distractor": true,
  "error_visibility": "low",
  "confidence_trap_type": "formal_word_bias",
  "correct_answer_flashiness": "low",
  "distractor_irresistibility_score": 0.88,
  "module_blueprint": {},
  "module_difficulty_ramp": "clustered_progressive",
  "answer_position_distribution": {},
  "recent_answer_bias_check": true,
  "option_length_balance_score": 0.91,
  "register_consistency_score": 0.94,
  "fatigue_pressure_index": 0.81,
  "trap_variety_score": 0.89,
  "module_release_ready": true
}
```

---

## Final Testing Rule

The generator must not ask only:

> Is the correct answer valid?

It must also ask:

> Why would a smart, rushed student pick each wrong answer?

If that cannot be answered convincingly, the distractor is not strong enough for production use.
