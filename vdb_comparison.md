# Vector DB Ground Truth Comparison

## Short Answer

Yes, generation would likely improve if a vector database were used for ground
truth retrieval, but only if it is used as a retrieval and calibration layer.

It should not replace the rule system.

## Main Judgment

A vector database would be better than the current state for generation quality,
especially for Craft and Structure items, because it can retrieve official or
approved near-neighbor questions that match the target skill, difficulty, trap
profile, and passage style.

However, embeddings alone cannot enforce:

- taxonomy legality
- domain separation
- distractor logic
- validator-safe output shape
- generation contracts

So the correct architecture is:

1. rules decide what is legal
2. vector retrieval supplies the closest ground-truth analogs
3. conformance and drift checks decide whether to accept or rerun

## Why A Vector DB Would Help

### 1. Better retrieval of official analogs

The current problem is not only that the rules are incomplete. It is also that
the generator is not reliably grounded in the closest official examples for the
exact requested item family.

A vector database can retrieve:

- nearest official Words in Context items
- nearest official Cross-Text Connections items
- nearest official Text Structure and Purpose items
- nearest official SEC items by trap, focus, or distractor profile

That gives the generator better local style guidance than a long monolithic
rules file alone.

### 2. Better answer-choice calibration

The current Craft problem is that answers often feel too obvious.

A vector retrieval layer can help by showing the generator:

- how close official distractors are to the correct answer
- how often wrong answers fail by scope, precision, tone, attribution, or
  relationship type
- how subtle official answer separation tends to be

This is especially useful for Craft and Structure, where realism depends more on
semantic competition than on grammar mechanics.

### 3. Better realism scoring

The current V3 rules already point toward this idea through:

- `official_similarity_score`
- `structural_similarity_score`
- anti-clone protection
- distractor competition scoring

A vector database gives a practical retrieval substrate for those checks.

Instead of judging realism only in the abstract, the system can compare a
generated item against the nearest official or approved ground-truth items.

## What The Repo Already Suggests

The existing docs already move in this direction.

### Existing vector retrieval concept

`docs/pipeline/llm_generation_workflow.md` describes vector similarity
selection using `question_embeddings` and pgvector for seed-question matching.

That means the repository already recognizes that semantic retrieval is useful
for generation.

### Existing corpus conformance concept

The same workflow document also describes corpus conformance checking against
`v_corpus_fingerprint`.

That is important because vector retrieval and corpus conformance solve
different problems:

- vector retrieval finds similar examples
- corpus conformance checks whether the generated annotation stays inside the
  expected distribution and legal target space

### Existing V3 realism hooks

`rules_agent_dsat_grammar_ingestion_generation_v3.md` already includes:

- `official_similarity_score`
- `structural_similarity_score`
- rewrite thresholds

So the logic for comparison exists conceptually, even if the runtime wiring is
not yet strong enough.

## What A Vector DB Will Not Fix By Itself

Using a vector database will not automatically solve the current issues.

It will not fix:

- the grammar-shaped generation prompt contract
- conflicts between reading and grammar domain rules
- weak Craft-specific distractor-generation instructions
- rule truncation or prompt-construction issues

If the generator still runs under a grammar-first output contract, vector
retrieval will improve style matching but will not fully correct the structural
mismatch.

## Best Use Cases For A Vector DB In This System

### 1. Pre-generation example retrieval

Before generation, retrieve the top 3-10 nearest official items for the
requested family and difficulty.

Examples:

- `words_in_context` + hard
- `cross_text_connections` + medium
- `subject_verb_agreement` + high trap intensity

### 2. Post-generation realism comparison

After generation, compare the new item against official nearest neighbors for:

- style similarity
- distractor distance
- passage structure similarity
- answer separation realism

### 3. Anti-clone enforcement

Use vector similarity plus structural checks to catch generated items that are
too close to released material.

### 4. Skill-family-specific retrieval

Craft items should retrieve Craft exemplars.

Grammar items should retrieve grammar exemplars.

The retrieval layer should not pool all families together without a domain or
family filter, because that would blur the generation target.

## Best Architecture

The strongest design is:

### Layer 1: Rules

Rules define:

- allowed fields
- allowed key combinations
- domain boundaries
- distractor requirements
- validation requirements

### Layer 2: Vector retrieval

Vector retrieval supplies:

- nearest approved official examples
- style anchors
- passage-shape analogs
- distractor realism anchors

### Layer 3: Conformance and drift

Conformance and drift checks enforce:

- target skill fidelity
- target difficulty fidelity
- legal annotation values
- distribution alignment
- rerun if critical mismatch is detected

## Final Recommendation

Yes, a vector database for ground truth would likely improve generation
materially, especially for Craft and Structure.

But it should be treated as a retrieval layer on top of a cleaned-up rules
architecture, not as a substitute for rules.

If implemented correctly, the likely outcome is:

- better exemplar selection
- less obvious answer choices
- more SAT-like distractor competition
- better realism scoring
- better anti-clone control

If implemented incorrectly, the likely outcome is:

- semantically similar examples with no enforcement of legality
- better style mimicry but continued structural mistakes
- persistent mismatch between prompt contract and target domain
