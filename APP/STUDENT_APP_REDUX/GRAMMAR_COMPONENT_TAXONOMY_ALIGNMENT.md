# Grammar Component — Taxonomy Alignment with Backend (v8 Rules)

## ✅ CONFIRMED ALIGNMENT

The component breakdown aligns with the DSAT Grammar Ingestion/Generation v8 rules file.

### Grammar Taxonomy (Backend → Frontend)

The `grammar-app.html` already uses the correct taxonomy structure:

| Concept | Backend Key (rules_v8) | HTML Example | Approved Values |
|---------|------------------------|--------------|-----------------|
| **Grammar Role** | `grammar_role_key` | "verb_form" | sentence_boundary, agreement, verb_form, modifier, punctuation, parallel_structure, pronoun, expression_of_ideas |
| **Grammar Focus** | `grammar_focus_key` | "verb_tense_consistency" | subject_verb_agreement, verb_tense_consistency, verb_form, voice_active_passive, etc. (40+ keys) |
| **Syntactic Trap** | `syntactic_trap_key` | ["temporal_sequence_ambiguity", "early_clause_anchor"] | none, nearest_noun_attraction, garden_path, early_clause_anchor, nominalization_obscures_subject, interruption_breaks_subject_verb, long_distance_dependency, pronoun_ambiguity, scope_of_negation, modifier_attachment_ambiguity, presupposition_trap, temporal_sequence_ambiguity, multiple |
| **Trap Intensity** | `syntactic_trap_intensity` | "medium" | low, medium, high |

---

## Two-Layer Grammar Key System

The HTML uses TWO distinct types of "grammar keys" that must NOT be confused:

### Layer 1: Structural Anatomy (UI-Level, for Explanation)

These are **explanatory structural elements** used to teach the student how to analyze a sentence:
- "Subordinate Clause"
- "Primary Subject"
- "Main Verb"
- "Relative Clause"
- "Modifier"
- "Subordinating Conjunction"

**Purpose:** Help students identify sentence parts and understand WHERE the rule applies.  
**Source:** Hardcoded in HTML (or fetched from a UI grammar reference API).  
**Group:** "Sentence Anatomy"

**These are NOT the same as `grammar_focus_key`.** They are pedagogical; they help students FIND the error, not classify it.

### Layer 2: Backend Taxonomy Keys (for Classification & Generation)

These are the **official SAT grammar classification keys** from rules_v8:
- "verb_form" (role_key)
- "verb_tense_consistency" (focus_key)
- "temporal_sequence_ambiguity" (trap_key)

**Purpose:** Classify the question for ingestion, generation, student weakness tracking, and analytics.  
**Source:** Fetched from backend API (part of the question's `classification` object).  
**Group:** "Approved Grammar Keys" (in HTML; in rules as Part D)

**These directly align with the rules file (D.1–D.5).**

---

## Data Structure: What the Backend Sends

When the `/api/questions?domain=verbal&focus=grammar` endpoint returns a question, it includes:

```json
{
  "id": "q-123",
  "text": "...",
  "options": [...],
  "classification": {
    "grammar_role_key": "verb_form",
    "grammar_focus_key": "verb_tense_consistency",
    "syntactic_trap_key": "temporal_sequence_ambiguity",
    "secondary_grammar_focus_keys": [],
    "student_failure_mode_key": "tense_proximity_pull"
  },
  "reasoning": {
    "primary_rule": "...",
    "trap_mechanism": "...",
    "correct_answer_reasoning": "...",
    "distractor_analysis_summary": "..."
  }
}
```

The frontend receives:
- ✅ `grammar_role_key` — directly from backend
- ✅ `grammar_focus_key` — directly from backend
- ✅ `syntactic_trap_key` — array, directly from backend
- ✅ `trap_mechanism` — directly from backend (in `reasoning`)

The frontend **does NOT** directly receive a pre-computed list of "writing style keys" or "formal_academic_register" from the backend. These appear to be **custom annotations added by the grammar-app.html** for a specific question, not a formal taxonomy.

---

## Component Breakdown: Required Corrections

### ❌ Issue in Original Breakdown

The breakdown defined:

```typescript
interface TrapAnalysis {
  grammarFocusKey: string
  syntacticTrapKeys: string[]
  writingStyleKeys: string[]  // ← NOT PART OF BACKEND
}
```

The `writingStyleKeys` are **NOT part of the formal backend taxonomy (v8)**. They are:
- Either custom per-question annotations (like "formal_academic_register", "contrast_signal")
- Or they should map to `student_failure_mode_key` values (from D.7)

### ✅ Corrected Data Structure

```typescript
interface GrammarQuestion {
  id: string
  text: string
  options: Option[]
  
  // Backend classification (from rules_v8)
  classification: {
    grammar_role_key: string       // D.1 keys
    grammar_focus_key: string      // D.2 keys
    syntactic_trap_key: string | string[]  // D.5 keys
    syntactic_trap_intensity: "low" | "medium" | "high"
    student_failure_mode_key: string  // D.7 keys
  }
  
  // Reasoning/explanation
  reasoning: {
    primary_rule: string
    trap_mechanism: string
    correct_answer_reasoning: string
    distractor_analysis_summary: string
  }
}

interface Option {
  id: string
  text: string
  correct: boolean
  student_failure_mode_key?: string  // Why this distractor is tempting
  explanation?: string
}
```

---

## Hook Implementation: Grammar Key Fetching

### What to Fetch on Mount

```typescript
// Fetch the question with full classification
const { data: question } = useQuery({
  queryKey: ['grammar-question'],
  queryFn: () => api.getQuestions({
    domain: 'verbal',
    focus: 'grammar',
    limit: 1
  })
})

// Optionally fetch reference documentation for grammar keys
const { data: grammarKeysCatalog } = useQuery({
  queryKey: ['grammar-keys-catalog'],
  queryFn: () => api.getGrammarKeysCatalog()
  // Returns: list of grammar_role_key, grammar_focus_key, syntactic_trap_key definitions
})
```

### What NOT to Fetch

- ❌ Do NOT fetch "writingStyleKeys" or "formalAcademicRegister" — these are custom per-question
- ❌ Do NOT fetch "Sentence Anatomy" keys — these are hardcoded UI reference material

---

## Rendering Grammar Keys: Two-Phase Approach

### Phase 1: Display Syntax Anatomy (Explanatory)

When rendering the sentence for analysis, highlight structural elements:
- "Subject": the main noun phrase
- "Main Verb": the primary action
- "Modifier": descriptive phrase
- Etc.

**Source:** Hardcoded in component or fetched from grammar reference API (not the question data).

### Phase 2: Display Trap & Classification (Analytical)

Show what the question ACTUALLY tests:
- **Grammar Role:** verb_form
- **Grammar Focus:** verb_tense_consistency
- **Trap Mechanism:** temporal_sequence_ambiguity
- **Why it's a trap:** "The opening subordinate clause and formal style make past perfect sound attractive..."

**Source:** From `classification` and `reasoning` in the question object.

---

## API Contract for Phase 1 Implementation

**Endpoint:** `POST /api/questions?domain=verbal&focus=grammar`

**Response must include:**
```json
{
  "id": "...",
  "text": "...",
  "options": [
    { "id": "A", "text": "...", "correct": true },
    { "id": "B", "text": "...", "correct": false },
    ...
  ],
  "classification": {
    "grammar_role_key": "verb_form",
    "grammar_focus_key": "verb_tense_consistency",
    "syntactic_trap_key": ["temporal_sequence_ambiguity", "early_clause_anchor"],
    "syntactic_trap_intensity": "medium"
  },
  "reasoning": {
    "primary_rule": "...",
    "trap_mechanism": "...",
    "correct_answer_reasoning": "...",
    "distractor_analysis_summary": "..."
  }
}
```

**Fallback:** If the backend does NOT yet provide `classification.syntactic_trap_key` as an array, the frontend should expect it as a single string and convert to array.

---

## Checklist Before Phase 1 Kickoff

- [ ] Confirm backend `/api/questions?domain=verbal&focus=grammar` returns `classification` object with all D.1–D.5 keys
- [ ] Confirm `syntactic_trap_key` structure (single string or array?) — if array, max length?
- [ ] Confirm `reasoning` object includes `trap_mechanism` text
- [ ] Decide: Should "Sentence Anatomy" keys (Subject, Modifier, etc.) be:
  - A. Hardcoded in the component?
  - B. Fetched from a separate grammar reference API?
  - C. Derived from passage token annotations in the backend response?
- [ ] Decide: How to map `student_failure_mode_key` (D.7) to distractor-specific explanations?

---

## Summary

✅ The component breakdown aligns with rules_v8 for taxonomy keys.

⚠️ Clarify the role of "writingStyleKeys" — not part of formal taxonomy; either custom per-question or should map to `student_failure_mode_key`.

✅ The two-layer system (Sentence Anatomy for teaching + Backend Taxonomy for classification) is correct and necessary.

🚀 Ready to implement Phase 1 once the above checklist is confirmed.
