Yes — you will want an **LLM ingestion method**.

The schema alone tells you **where** data goes. You still need a repeatable process that tells the model **how to read a question, classify it, analyze options, and output valid structured records**.

The best setup is not “let the LLM write directly to the database.”  
The best setup is:

1. **extract**

2. **normalize**

3. **validate**

4. **only then insert/upsert**

## What the LLM should do

Use the LLM for the parts that are hard to code with rules alone:

- classify the question

- identify subskill

- label distractor types

- explain why each wrong answer is tempting

- write solver steps

- assign generation pattern family

Use deterministic code for:

- checking allowed values

- enforcing foreign keys

- verifying required fields

- converting to SQL or Supabase inserts

- rejecting malformed outputs

## Recommended ingestion architecture

### Stage 1: raw capture

Store the raw item first:

- prompt text

- passage text

- answer choices

- correct answer

- source metadata

This can come from PDF parsing, manual entry, or OCR if needed.

### Stage 2: LLM classification

Give the LLM:

- the raw question

- the answer choices

- your taxonomy rules

- the allowed enum/lookup values

Have it return **strict JSON** matching your ingestion contract.

### Stage 3: validator

Run a validator in Python or TypeScript that checks:

- required fields are present

- lookup keys exist

- option labels are A/B/C/D

- exactly one option is correct

- `correct_option_label` matches the correct option row

- fields like `question_family_key`, `solver_pattern_key`, `generation_pattern_family_key` are allowed values

- JSONB arrays are arrays, not strings pretending to be arrays

### Stage 4: review

For official content, it is smart to keep:

- `ingestion_status = draft / reviewed / approved`

- `ingestion_source = llm / human / hybrid`

### Stage 5: upsert

Only validated rows get inserted into:

- `questions`

- `question_classifications`

- `question_options`

- `question_reasoning`

- `question_generation_profiles`

## The key to consistency

Consistency comes from giving the LLM **three things**:

### 1. A fixed ontology reference

You need a compact reference sheet of:

- allowed question families

- allowed answer mechanisms

- allowed solver patterns

- allowed distractor types

- allowed semantic relations

- allowed plausibility sources

- allowed generation pattern families

Do not ask the LLM to invent labels freely.

### 2. A fixed output contract

Require one exact JSON shape every time.

Example top-level structure:

```json
{
  "question": {},
  "classification": {},
  "options": [],
  "reasoning": {},
  "generation_profile": {}
}
```

### 3. Decision rules

For each field, define how to choose it.

For example:

- `question_family_key`: choose the narrowest stable family that best describes the item’s primary task

- `answer_mechanism_key`: choose the mechanism the student must use to solve the item

- `distractor_type_key`: assign the main reason the option is wrong

- `semantic_relation_key`: assign how the wrong option differs from the correct one

- `plausibility_source_key`: assign why a student might still choose it

Without these rules, outputs drift.

## Best practice: use a two-pass LLM workflow

A single pass can work, but a **two-pass workflow** is usually more consistent.

### Pass 1: extraction

Have the model extract only:

- stem

- passage

- choices

- correct answer

- source metadata

No taxonomy yet.

### Pass 2: annotation

Feed the extracted structured item into a second prompt that does:

- classification

- option analysis

- reasoning

- generation profile

This reduces hallucinated structure.

## Prompting pattern that works well

Use a system instruction like:

```text
You are annotating DSAT Reading and Writing questions into a fixed schema.
You must only use allowed keys from the provided lookup lists.
Do not invent labels.
If uncertain, choose the closest allowed label and explain uncertainty in review_notes.
Return valid JSON only.
```

Then provide:

- the schema contract

- the allowed lookup values

- 2 to 5 annotated examples

- the raw item

## You should include field-by-field rules

For example:

```text
question_family_key:
- Use "words_in_context" for precise vocabulary completion items.
- Use "conventions_grammar" for grammar/punctuation items.
- Use "supporting_detail" for direct retrieval questions.
- Use "weaken_hypothesis" when the task is to find evidence that weakens a claim.
```

And:

```text
plausibility_source_key:
- Use "grammar_fit_only" when the wrong choice mainly looks acceptable because it fits the sentence grammatically.
- Use "topical_association" when the wrong choice is tempting because it belongs to the same topic domain.
- Use "formal_register_match" when it sounds academic or polished but is still wrong.
```

This makes a big difference.

## Add confidence and review flags

For production ingestion, add fields like:

- `annotation_confidence`

- `needs_review`

- `review_notes`

The LLM should mark low-confidence cases instead of forcing certainty.

Example:

- quote-selection questions

- rhetorical synthesis with subtle audience differences

- sentence-function questions with close distractors

## Strong recommendation: create an ingestion JSON schema

Use Pydantic or JSON Schema.

Example idea:

```python
class QuestionRecord(BaseModel):
    question: QuestionPayload
    classification: ClassificationPayload
    options: list[OptionPayload]
    reasoning: ReasoningPayload
    generation_profile: GenerationProfilePayload
```

Then validate:

- enums

- lengths

- nullability

- uniqueness of option labels

- one correct answer only

This turns LLM output into something safe.

## Practical workflow for your stack

Since you're targeting Supabase + vector, a good pipeline is:

- Python or FastAPI ingestion service

- raw item stored in staging table

- LLM annotates into JSON

- Pydantic validates

- service maps JSON to SQL upserts

- approved rows move into production tables

- embedding job runs after insert

## Suggested table for ingestion staging

You may want one extra table:

`question_ingestion_jobs`

with fields like:

- `id`

- `source_file`

- `raw_text`

- `raw_json`

- `llm_output_json`

- `validation_errors_json`

- `status`

- `review_notes`

- `created_at`

This makes debugging much easier.

## The most important rule

Do **not** let the LLM write directly into the schema without a validator layer.

Use the LLM as:

- a structured annotator

Not as:

- the final source of truth

## What to build next

The best next artifact is an **LLM ingestion contract**:

- exact JSON schema

- allowed lookup values

- field-by-field annotation rules

- 2 to 4 worked examples

That becomes the instruction set you reuse every time.
