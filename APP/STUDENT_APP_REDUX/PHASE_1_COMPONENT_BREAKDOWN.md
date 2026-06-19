# Phase 1: Grammar Practice Page — Component Breakdown

## Overview

Port `grammar-app.html` into a React component system. The page consists of:
1. **Header** — Title, progress indicator
2. **Question Section** — Sentence with blanks, answer options, feedback
3. **Grammar Analysis** — Grammar keys grid, trap summary, explanations
4. **Controls** — Clear keys, Find traps buttons

---

## Data Structures

### ⚠️ Two-Layer Grammar Key System

**Layer 1: Sentence Anatomy Keys** (UI-Level, for Explanation)
- Examples: "Subordinate Clause", "Primary Subject", "Main Verb", "Relative Clause"
- **Purpose:** Help students understand WHERE the error is located
- **Source:** Hardcoded reference or separate grammar reference API
- **NOT part of backend classification**

**Layer 2: Backend Taxonomy Keys** (from rules_agent_v8)
- Grammar Role: `grammar_role_key` (D.1) — e.g., "verb_form"
- Grammar Focus: `grammar_focus_key` (D.2) — e.g., "verb_tense_consistency"
- Syntactic Trap: `syntactic_trap_key` (D.5) — e.g., "temporal_sequence_ambiguity"
- **Purpose:** Classify question for ingestion, generation, tracking
- **Source:** Backend API response (`classification` object)

See GRAMMAR_COMPONENT_TAXONOMY_ALIGNMENT.md for full details.

---

### SyntaxAnatomyKey (UI Reference, Hardcoded)
```typescript
interface SyntaxAnatomyKey {
  id: string
  label: string           // e.g., "Primary Subject"
  group: string           // "Sentence Anatomy"
  color: string
  lightBg: string
  description: string
  rule: string
  priority: number
}
```

### BackendGrammarClassification (from rules_v8)
```typescript
interface BackendGrammarClassification {
  grammar_role_key: string           // D.1: sentence_boundary, agreement, verb_form, etc.
  grammar_focus_key: string          // D.2: subject_verb_agreement, verb_tense_consistency, etc.
  syntactic_trap_key: string | string[]  // D.5: nearest_noun_attraction, temporal_sequence_ambiguity, etc.
  syntactic_trap_intensity: "low" | "medium" | "high"
  student_failure_mode_key?: string  // D.7: why students pick wrong answers
  secondary_grammar_focus_keys?: string[]
}
```

### Option
```typescript
interface Option {
  id: string              // "A", "B", "C", "D"
  text: string
  correct: boolean
  student_failure_mode_key?: string  // Why this distractor is tempting (D.7)
}
```

### GrammarQuestion (Backend Response)
```typescript
interface GrammarQuestion {
  id: string
  text: string                        // Full question prompt
  options: Option[]
  
  // Backend classification (from rules_v8, Part D)
  classification: BackendGrammarClassification
  
  // Reasoning & explanation
  reasoning: {
    primary_rule: string              // The grammar rule that selects correct answer
    trap_mechanism: string            // How the syntactic trap misleads test-takers
    correct_answer_reasoning: string  // Step-by-step justification
    distractor_analysis_summary: string
  }
  
  // Optional: test metadata
  source_exam?: string                // "PT1", "PT4", "GENERATED"
  source_question_number?: number
  explanation_short?: string
}
```

### SentenceStructure (for rendering with Anatomy annotations)
```typescript
interface Token {
  id: string
  text: string
  syntaxAnatomy?: {
    key_id: string        // e.g., "subject", "main_verb", "modifier"
    anatomyKey: SyntaxAnatomyKey
  }
}
```

---

## Custom Hook: `useGrammarSession`

**File:** `src/hooks/useGrammarSession.ts`

### State
```typescript
{
  sentence: GrammarQuestion | null
  selectedAnswer: string | null
  activeKeys: Set<string>
  feedbackVisible: boolean
  sentenceIndex: number
  totalSentences: number
}
```

### 11 Core Functions

1. **`renderSentence()`**
   - Takes `tokens` array from current sentence
   - Renders sentence with blanks replaced by selected answer (or "___")
   - Returns: HTML string or React elements
   - Styling: sentence-box class with highlighted blanks

2. **`renderOptions()`**
   - Takes `options` array from current sentence
   - Renders buttons for each option
   - Highlights correct/incorrect based on selection
   - Returns: Rendered option buttons
   - Event: `selectAnswer()` on click

3. **`renderGrammarKeys()`** — Syntax Anatomy Keys (UI Reference Layer)
   - Takes hardcoded SYNTAX_ANATOMY_KEYS (from grammar-app.html structure)
   - Groups by `group` property (e.g., "Sentence Anatomy")
   - Renders as clickable educational key buttons
   - Highlights active keys (in `activeKeys` set) to show WHERE the rule applies
   - Returns: Grouped key cards with buttons
   - Event: `toggleKey()` on click
   - **Note:** These are for teaching students to analyze sentences, NOT for classification

4. **`renderTrapSummary()`** — Backend Taxonomy Display
   - Takes `classification` object from backend (grammar_role_key, grammar_focus_key, syntactic_trap_key)
   - Displays: Grammar Role, Grammar Focus, Syntactic Trap(s)
   - Shows trap intensity (low/medium/high)
   - Maps keys to human-readable labels (from rules_v8 definitions)
   - Returns: HTML/component showing identified trap pattern
   - Styling: trap-summary class
   - **Note:** This is what DSAT actually tests, not the syntax anatomy

5. **`renderExplanations()`** — Combined Layer Explanation
   - Takes `selectedAnswer`, `reasoning` (from backend), and `activeKeys` (syntax anatomy)
   - Shows explanation text from `reasoning.correct_answer_reasoning`
   - Links active syntax anatomy keys to where the rule applies
   - Shows why the answer is correct (or incorrect)
   - Returns: Explanation text + related keys
   - Styling: feedback class (correct/incorrect variant)

6. **`selectAnswer(optionId)`**
   - Sets `selectedAnswer` to optionId
   - Sets `feedbackVisible` to true
   - Updates sentence rendering to show selected text
   - **Event handler**: called when user clicks an option
   - Triggers: `renderSentence()`, `renderFeedback()` re-render

7. **`renderFeedback()`**
   - Takes `selectedAnswer` and current sentence's correct answer
   - Displays "Correct!" or "Incorrect" with styling
   - Shows explanation from sentence.explanation
   - Shows correct answer if wrong
   - Returns: Feedback card (correct/incorrect variant)
   - Styling: feedback class with .correct or .incorrect

8. **`toggleKey(keyId)`**
   - Adds/removes keyId from `activeKeys` set
   - Toggles visual highlight on that key button
   - **Event handler**: called when user clicks a grammar key
   - Triggers: `renderGrammarKeys()` re-render

9. **`clearKeys()`**
   - Clears all items from `activeKeys` set
   - Removes all key highlights
   - **Event handler**: called by "Clear Keys" button
   - Triggers: `renderGrammarKeys()` re-render

10. **`findTraps()`** — Auto-Highlight Relevant Anatomy Keys
    - Reads `classification.grammar_focus_key` from backend
    - Maps it to relevant syntax anatomy keys (e.g., "verb_tense_consistency" → highlight "Main Verb")
    - Populates `activeKeys` with anatomy key IDs related to this question's trap
    - **Event handler**: called by "Find Traps" button
    - Triggers: `renderGrammarKeys()` re-render with highlights
    - **Note:** Uses backend classification to intelligently highlight syntax anatomy

11. **`getKey(keyId)`** (helper)
    - Looks up a syntax anatomy key by ID in SYNTAX_ANATOMY_KEYS
    - Returns: SyntaxAnatomyKey object or null
    - Used by: `renderGrammarKeys()`, `renderExplanations()`, internal
    - **Note:** Works ONLY with Syntax Anatomy layer, not backend taxonomy

### Helper Functions (not separately listed but essential)
- **`findActiveKey()`** — Filter GRAMMAR_KEYS by activeKeys set
- All functions should maintain immutability (no direct mutations)

---

## API Integration

### ✅ Confirmed Backend Response Structure

Based on rules_agent_v8.md, the backend will return:

```json
{
  "id": "q-123",
  "text": "The researcher, who had spent years on this project, _______ their findings with the team.",
  "options": [
    { "id": "A", "text": "shares", "correct": false },
    { "id": "B", "text": "shared", "correct": true },
    { "id": "C", "text": "had shared", "correct": false },
    { "id": "D", "text": "is sharing", "correct": false }
  ],
  "classification": {
    "grammar_role_key": "verb_form",
    "grammar_focus_key": "verb_tense_consistency",
    "syntactic_trap_key": ["temporal_sequence_ambiguity", "early_clause_anchor"],
    "syntactic_trap_intensity": "medium",
    "student_failure_mode_key": "tense_proximity_pull"
  },
  "reasoning": {
    "primary_rule": "Choose verb tense required by main clause time frame, not tense that sounds more formal.",
    "trap_mechanism": "The introductory subordinate clause and formal SAT style make past perfect sound attractive, but main clause 'shared' sets completed-past frame.",
    "correct_answer_reasoning": "The main verb must be simple past (shared) to match the time frame established by the action.",
    "distractor_analysis_summary": "Options C and D offer more complex tenses; option A uses present tense."
  },
  "source_exam": "PT4",
  "source_question_number": 23
}
```

### Fetch Points

**On component mount:**
1. `POST /api/questions?domain=verbal&focus=grammar&limit=1`
   - Returns: `GrammarQuestion` (single question with full `classification` + `reasoning`)
   - Store: sentence, options, classification, reasoning

2. (Optional for Phase 1) `GET /api/grammar/keys/reference`
   - Returns: List of all grammar_role_key, grammar_focus_key, syntactic_trap_key definitions
   - Purpose: Build a lookup table for displaying key names/descriptions

3. (Hardcoded for Phase 1) Sentence Anatomy Keys
   - Keep hardcoded in component (from grammar-app.html: Subject, Main Verb, Modifier, etc.)
   - These are UI reference material, not backend data

### On User Actions

4. `POST /api/submit` (when answer selected)
   - Body: 
     ```json
     {
       "question_id": "q-123",
       "selected_option_id": "B",
       "user_token": "test-token-xyz"
     }
     ```
   - Returns:
     ```json
     {
       "correct": true,
       "explanation": "...",
       "next_question_id": "q-124"
     }
     ```

### Pre-Implementation Validation

**BEFORE Phase 1 starts, verify:**
- [ ] Backend `/api/questions` endpoint returns `classification` object with all required keys
- [ ] `syntactic_trap_key` is an array (e.g., `["temporal_sequence_ambiguity", "early_clause_anchor"]`)
- [ ] `reasoning` object includes `primary_rule`, `trap_mechanism`, `correct_answer_reasoning`
- [ ] `student_failure_mode_key` is provided (or document if missing)
- [ ] `/api/submit` endpoint exists and returns correct/incorrect + next question ID

---

## React Component: `GrammarPractice`

**File:** `src/components/GrammarPractice.tsx`

### Props
```typescript
interface GrammarPracticeProps {
  userToken?: string  // For auth to API
  onQuestionComplete?: (result: SubmissionResult) => void
}
```

### Component Structure
```
<GrammarPractice>
  ├── <Header>
  │   ├── Title "SAT Grammar Practice"
  │   └── Progress (e.g., "Question 1 of 10")
  │
  ├── <QuestionSection>
  │   ├── <SentenceDisplay>  // renderSentence()
  │   ├── <OptionsContainer> // renderOptions()
  │   └── <FeedbackBox>      // renderFeedback()
  │
  └── <GrammarAnalysisSection>
      ├── <GrammarKeysGrid>  // renderGrammarKeys()
      ├── <TrapSummaryBox>   // renderTrapSummary()
      ├── <ExplanationsPanel> // renderExplanations()
      └── <ActionButtons>    // "Find Traps", "Clear Keys"
```

### Sub-Components

1. **`<Header />`**
   - Displays: Icon, Title, Progress
   - Props: currentQuestion, totalQuestions
   - Styling: header, header-left, progress-container classes

2. **`<QuestionSection />`**
   - Container for sentence, options, feedback
   - Props: sentence, selectedAnswer, feedbackVisible
   - Events: onSelectAnswer, onAnswerSubmitted
   - Styling: question-section, sentence-box, options, feedback classes

3. **`<SentenceDisplay />`**
   - Renders sentence tokens with blanks
   - Highlights selected answer text in blank
   - Props: tokens, selectedAnswerText
   - Styling: sentence-box, token, blank classes
   - Component: Calls renderSentence()

4. **`<OptionsContainer />`**
   - Grid of answer option buttons
   - Props: options, selectedOptionId, isAnswered
   - Events: onSelectOption
   - Styling: options, option-btn, option-btn.selected classes
   - Component: Calls renderOptions()

5. **`<FeedbackBox />`**
   - Shows "Correct!" or "Incorrect" with explanation
   - Props: isVisible, isCorrect, explanation, correctOptionId
   - Styling: feedback, feedback.correct, feedback.incorrect classes
   - Component: Calls renderFeedback()

6. **`<GrammarKeysGrid />`**
   - Groups of grammar key buttons
   - Props: grammarKeys, activeKeyIds
   - Events: onToggleKey
   - Styling: grammar-keys, key-group, key-group-buttons, key-btn classes
   - Component: Calls renderGrammarKeys()

7. **`<TrapSummaryBox />`**
   - Shows detected trap profile (Grammar Rule, Trap Mechanism, Style Cues)
   - Props: trapAnalysis, grammarKeys
   - Styling: trap-summary, trap-summary-grid classes
   - Component: Calls renderTrapSummary()

8. **`<ExplanationsPanel />`**
   - Detailed explanation of correct answer
   - Links to related grammar keys
   - Props: explanation, relatedKeyIds, grammarKeys
   - Styling: explanations, explanation-item classes
   - Component: Calls renderExplanations()

9. **`<ActionButtons />`**
   - "Find Traps" and "Clear Keys" buttons
   - Events: onFindTraps, onClearKeys
   - Styling: btn-action, find-btn, clear-btn classes

---

## Styling Strategy

### CSS Framework
- **Base:** Tailwind CSS (already installed)
- **Goal:** Port original CSS variables + layout from grammar-app.html
- **Approach:** Use Tailwind classes + custom CSS for complex layouts (if needed)

### Color Scheme (from grammar-app.html)
```
Primary: #667eea (purple)
Primary Dark: #764ba2
Success: #16a34a (green)
Error: #ef4444 (red)
Warning: #d97706 (orange)
Info: #2563eb (blue)

Grays: #f9fafb - #111827
```

### Layout Components
- Container: max-width 960px, centered
- Header: flex, space-between, white background
- Question section: white card, shadow
- Grammar section: white card, shadow
- Grid layouts: flex with gap

### Animations (Framer Motion for Phase 4)
- Fade in on mount
- Slide transitions between questions
- Highlight animations on key toggle
- Feedback reveal animation

---

## Hook Implementation Details

### State Management
- Use `useState` for all state variables
- Use `useEffect` for API calls on mount
- Use `useCallback` for event handlers (to avoid re-renders)
- Consider `useReducer` if state becomes complex

### Key State Objects

```typescript
{
  // Backend question data
  question: GrammarQuestion | null
  
  // User interaction state
  selectedAnswer: string | null
  activeKeys: Set<string>              // Syntax Anatomy keys, NOT backend keys
  feedbackVisible: boolean
  
  // Progress tracking
  sentenceIndex: number
  totalSentences: number
  
  // Error handling
  isLoading: boolean
  error: string | null
}
```

### Data Flow & Two-Layer System

```
useGrammarSession Hook:
  ├── Fetch GrammarQuestion from backend (includes classification + reasoning)
  ├── Initialize hardcoded SYNTAX_ANATOMY_KEYS
  ├── Maintain selected answer state
  ├── Maintain active syntax anatomy keys state
  ├── Provide all 11 render functions + helpers
  └── Return state + handlers to component
        ├── question (backend: classification, reasoning)
        ├── activeKeys (frontend: syntax anatomy highlights)
        └── handlers (selectAnswer, toggleKey, findTraps, etc.)

GrammarPractice Component:
  ├── Consume hook output (backend classification + syntax anatomy state)
  ├── Render sentence with anatomy annotations
  ├── Display trap summary (from backend classification)
  ├── Display explanation (from backend reasoning + active anatomy keys)
  ├── Render anatomy key buttons (from hardcoded list)
  └── Update hook state on user events
```

### Layer Separation

**Backend Layer (immutable, from API):**
- `question.classification` — grammar_role_key, grammar_focus_key, syntactic_trap_key
- `question.reasoning` — primary_rule, trap_mechanism, correct_answer_reasoning

**Frontend Layer (mutable, from component state):**
- `activeKeys` — which syntax anatomy keys are currently highlighted
- `selectedAnswer` — which option the student clicked
- `feedbackVisible` — whether to show feedback

### Error Handling
- API call failures: display error state, allow retry
- Missing data: fallbacks (e.g., show "Loading..." vs empty state)
- Invalid answers: validation before submission

---

## Testing Checklist (Phase 1.6 Integration Tests)

- [ ] renderSentence() renders tokens correctly
- [ ] renderOptions() renders all options clickable
- [ ] renderGrammarKeys() groups keys by category
- [ ] renderTrapSummary() shows correct trap analysis
- [ ] renderExplanations() shows correct/incorrect feedback
- [ ] selectAnswer() updates selected state + feedback
- [ ] renderFeedback() shows correct styling for correct/incorrect
- [ ] toggleKey() adds/removes key from activeKeys
- [ ] clearKeys() clears all activeKeys
- [ ] findTraps() populates activeKeys with trap keys
- [ ] getKey() returns correct grammar key by ID
- [ ] Full flow: load → select → submit → feedback → next (or clear/find traps)

---

## Dependencies & Imports

### Packages Already Installed
- `react` — Components, hooks
- `react-dom` — Rendering
- `react-router-dom` — Navigation (if routing between questions)
- `@tanstack/react-query` — API calls (optional, or use fetch)
- `tailwindcss` — Styling
- `@radix-ui/*` — Accessible UI components (optional)

### Custom Imports (to create)
- `src/types/index.ts` — Type definitions
- `src/api/client.ts` — API functions
- `src/hooks/useGrammarSession.ts` — Main hook
- `src/components/GrammarPractice.tsx` — Main component

---

## Timeline Estimate

| Task | Est. Time |
|------|-----------|
| 1.1 useGrammarSession hook | 2-3 hours |
| 1.2 GrammarPractice component + sub-components | 3-4 hours |
| 1.3 Router setup | 0.5 hours |
| 1.4 Unit tests | 1-2 hours |
| 1.5 Component tests | 2-3 hours |
| 1.6 Integration tests | 1-2 hours |
| 1.7 Design verification | 1-2 hours |
| 1.8 Performance validation | 0.5-1 hour |
| **Total Phase 1** | **11-18 hours** |

---

## Key Decisions Before Implementation

### ✅ RESOLVED by Taxonomy Alignment

1. **Two-layer system:** 
   - **Syntax Anatomy Keys:** Hardcoded in component (from grammar-app.html structure)
   - **Backend Taxonomy:** Fetched from API (classification object from rules_v8)
   - See GRAMMAR_COMPONENT_TAXONOMY_ALIGNMENT.md for details

### ⚠️ STILL TO DECIDE

2. **Routing:** Should each sentence be a separate route `/practice/grammar/1`, or paginated on same page?

3. **State persistence:** Should selected answers/active keys persist if user navigates away?

4. **Animations:** Use CSS transitions only, or Framer Motion? (Framer Motion for Phase 4)

5. **Testing:** Unit test with Vitest/Jest, or skip to component tests with React Testing Library?

6. **Syntax Anatomy → Backend Mapping:** How should `findTraps()` map backend `grammar_focus_key` to syntax anatomy keys?
   - Example: "verb_tense_consistency" → highlight "Main Verb" key?
   - Need explicit mapping table or heuristic?

7. **Student Failure Mode Display:** How to use `student_failure_mode_key` (D.7) when showing distractors?
   - Example: when answer is wrong, show "Why this answer is tempting: {failure_mode_key}"?

---
