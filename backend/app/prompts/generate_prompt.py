"""Generation prompt — produces new DSAT-style questions from a specification."""
import json
import os


_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_GENERATION_RULE_FILES = [
    ("Grammar v8", "rules_agent_dsat_grammar_ingestion_generation_v8.md"),
    ("Reading v3", "rules_agent_dsat_reading_v3.md"),
]


def _extract_between(text: str, start_marker: str, end_marker: str | None = None) -> str:
    start = text.find(start_marker)
    if start == -1:
        return ""
    if end_marker:
        end = text.find(end_marker, start + len(start_marker))
        return text[start:end] if end != -1 else text[start:]
    return text[start:]


def _extract_sections(text: str, sections: list[tuple[str, str | None]]) -> str:
    return "\n\n".join(
        chunk for start, end in sections if (chunk := _extract_between(text, start, end)).strip()
    )


def _generation_sections(label: str, rules_text: str) -> str:
    if label == "Grammar v8":
        return _extract_sections(
            rules_text,
            [
                ("## Purpose", "# PART A"),
                ("# PART A", "# PART B"),
                ("## B.1 Generation Input Specification", "## B.2"),
                ("## B.2 Step-by-Step Generation Workflow", "## B.3"),
                ("## B.3.0 Sub-Pattern Policy and Evidence Tiers", "## B.4"),
                ("## B.4 Distractor Generation Heuristics by Grammar Focus", "## B.5"),
                ("## B.5 Transition Subtype Vocabulary", "## B.6"),
                ("## B.6 Notes Synthesis Metadata", "## B.7"),
                ("## B.8 Difficulty Calibration for Generation", "## B.9"),
                ("## B.9 Batch, Deduplication, and Option Ordering", "## B.10"),
                ("## B.10 Explanation Requirements", "## B.11"),
                ("## B.13 Generation Validation Checklist", "## B.14"),
                ("## D.3 Disambiguation Rules", "## D.4"),
                ("## D.5 Syntactic Trap Keys", "## D.6"),
                ("## D.7 Student Failure Mode Keys", "## D.8"),
                ("## D.8 Schema Guardrails and Enforcement", "## D.9"),
                ("# PART E", "## Reference Quick-Index"),
            ],
        )
    if label == "Reading v3":
        return _extract_sections(
            rules_text,
            [
                ("## Purpose", "## Source Authority"),
                ("## 2. Required Output Shape", "## 3."),
                ("## 3. Question Fields", "## 8."),
                ("## 8. Answer Mechanism Keys", "## 13."),
                ("## 13. Skill-Specific Annotation Rules", "## 14."),
                ("## 14. Difficulty Calibration", "## 15."),
                ("## 15. Passage Architecture Requirements", "## 16."),
                ("## 16. Generation Rules", "## 17."),
                ("## 17. Disambiguation Rules", "## 18."),
                ("## 19. Student Failure Mode Keys", "## 20."),
                ("## 21. Validator Checklist", "## 22."),
                ("## 22. Passage Style Fingerprint", "## 23."),
                ("## 23. Generation Protocol", "## Appendix"),
            ],
        )
    return rules_text


def _infer_generation_domain(generation_request: dict) -> str:
    if any(
        generation_request.get(key)
        for key in (
            "target_reading_focus_key",
            "target_skill_family_key",
            "reading_focus_key",
            "reading_skill_family_key",
        )
    ):
        return "reading"
    family = str(generation_request.get("question_family_key") or "").lower()
    if family in {"craft_and_structure", "information_and_ideas"}:
        return "reading"
    if any(
        generation_request.get(key)
        for key in (
            "target_grammar_focus_key",
            "target_grammar_role_key",
            "grammar_focus_key",
            "grammar_role_key",
            "target_syntactic_trap_key",
        )
    ):
        return "grammar"
    return "both"


def _load_generation_rule_context(domain: str = "both") -> str:
    sections: list[str] = []
    for label, filename in _GENERATION_RULE_FILES:
        if domain == "grammar" and label != "Grammar v8":
            continue
        if domain == "reading" and label != "Reading v3":
            continue
        path = os.path.join(_ROOT_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            rules_text = f.read()
        body = _generation_sections(label, rules_text)
        sections.append(f"{label} RULES REFERENCE:\n{body}")
    return "\n\n".join(sections)


GENERATE_SYSTEM_PROMPT = """You are a DSAT question generation specialist following the current DSAT grammar and reading guide specifications.

Work through these phases in order, silently, before writing final output. Each phase's
result constrains the next — do not write the passage before Phase 1 is fixed, and do not
write options before the passage exists.

PHASE 1 — Profile. Fix generation_profile first: target skill/focus/trap keys, passage
architecture (if any), difficulty, and — critically — a target_distractor_pattern naming
each wrong option's failure type BEFORE the passage is drafted. Distractors bolted on after
the fact tend to share one failure reason; deciding the three distinct failure types up
front prevents that.

PHASE 2 — Passage. Draft the passage to the length and register the rules reference below
specifies for this item's stimulus/skill type. Reread it once and check, sentence by
sentence: length variation, hedging/attribution language, at least one appositive or
definitional aside for any technical term, and that no required piece of evidence for the
correct answer sits more than one sentence away from where it is needed. If the draft
fails any check, rewrite the passage — do not patch around it in the options.

PHASE 3 — Stem. Use the canonical stem wording for the declared stem_type_key.

PHASE 4 — Options. Write the correct option first, tied to a specific quoted or
paraphrased span of the passage. Then write each distractor to its assigned failure type
from Phase 1. For every distractor whose wrongness depends on a causal, comparative, or
directional claim (e.g. "X increases/decreases Y," "A is more/less than B"): explicitly
restate what that claim would predict if it were true, and confirm that prediction
contradicts — not accidentally matches — the passage's actual stated result. This check
catches the single most common generation failure: a distractor that is meant to be wrong
but, worked through, is actually consistent with the passage. Confirm no two distractors
fail for the same reason, and that at least two of the four options would survive a
skimming first read (an option only a highly attentive reader eliminates immediately is a
weak distractor).

PHASE 5 — Self-check. Before emitting output, verify: every option has a distinct
distractor_type_key and a why_wrong naming a specific textual defeater; the correct option
is not the longest, most hedged, or most detailed option by construction; no invented
key or field exists outside the ones this prompt and the rules reference define; if a
reasoning trap or passage architecture was declared, the passage actually instantiates it.

Your final output must include:
1. question: passage_text, question_text, options (4 labeled A-D), correct_option_label
2. classification: domain-appropriate keys and difficulty fields
   - Grammar / Expression of Ideas: grammar_role_key, grammar_focus_key, syntactic_trap_key
   - Reading: question_family_key, reading_skill_family_key, reading_focus_key; grammar keys null
3. options: per-option analysis with distractor_type_key, why_plausible, why_wrong, precision_score
4. reasoning: primary_rule, trap_mechanism, correct_answer_reasoning
5. generation_profile: target keys, passage_template, frequency_band
6. review: annotation_confidence, needs_human_review
7. self_check: {distractor_directions_verified: bool, failure_types_distinct: bool,
   architecture_instantiated: bool, notes: string — anything the checks above caught and
   fixed, or "none" if the first draft already passed}

Rules:
- Passage must be 20-40 words for sentence_only items
- Formal academic register, no contractions or slang
- Self-contained meaning (no outside knowledge needed) — every premise the correct answer
  depends on, including any experimental manipulation and its trigger, must appear on the
  page, not be assumed
- At least one grammar distractor must target the declared syntactic trap
- At least one reading distractor must target the declared reasoning trap or test construct
- No two distractors may fail for the exact same reason
- correct option may appear in any position (A-D)
- Output valid JSON only"""


def build_generate_prompt(generation_request: dict, source_examples: list = None) -> tuple[str, str]:
    """Build system and user prompts for question generation."""
    rules_context = _load_generation_rule_context()
    user_parts = [f"Generation request:\n{json.dumps(generation_request, indent=2)}"]
    if source_examples:
        user_parts.append(
            "\nStored official questions are serving as the foundational source for generation. "
            "Use these examples to calibrate DSAT style, taxonomy, passage architecture, "
            "distractor construction, and difficulty. Do not copy passages, stems, or options.\n"
            f"{json.dumps(source_examples, indent=2)}"
        )
    user = "\n".join(user_parts)
    system = GENERATE_SYSTEM_PROMPT
    if rules_context:
        system = f"{system}\n\n{rules_context}"
    return system, user


def build_generate_prompt_parts(
    generation_request: dict,
    source_examples: list = None,
) -> tuple[str, str, str]:
    """Return (system_static, system_dynamic, user) for prompt-cached generation calls.

    system_static  — grammar v8 + reading v3 generation sections; mark with cache_control
                     on Anthropic or use as num_keep prefix on Ollama. Domain-filtered
                     when the request clearly targets one domain.
    system_dynamic — GENERATE_SYSTEM_PROMPT base instructions; brief and stable.
    user           — the generation request JSON + optional source examples; fresh each call.
    """
    domain = _infer_generation_domain(generation_request)
    system_static = _load_generation_rule_context(domain)
    system_dynamic = GENERATE_SYSTEM_PROMPT

    user_parts = [f"Generation request:\n{json.dumps(generation_request, indent=2)}"]
    if source_examples:
        user_parts.append(
            "\nStored official questions are serving as the foundational source for generation. "
            "Use these examples to calibrate DSAT style, taxonomy, passage architecture, "
            "distractor construction, and difficulty. Do not copy passages, stems, or options.\n"
            f"{json.dumps(source_examples, indent=2)}"
        )
    user = "\n".join(user_parts)
    return system_static, system_dynamic, user
