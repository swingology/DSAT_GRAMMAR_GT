"""TASK-026 — span_label.py unit tests.

Covers generate_span_label with known PREFIX_MAP entries, anatomy suffix,
trap bracket annotation, and the 80-char truncation ceiling.
"""
from app.services.span_label import generate_span_label


class TestPrefix:
    def test_known_key_uses_prefix_map(self):
        label = generate_span_label("subject_verb_agreement", [], [])
        assert label.startswith("SVA")

    def test_known_comma_key(self):
        label = generate_span_label("punctuation_comma", [], [])
        assert label.startswith("Comma mechanics")

    def test_unknown_key_falls_back_to_title_case(self):
        label = generate_span_label("some_new_key", [], [])
        assert label.startswith("Some New Key")

    def test_none_key_falls_back_to_grammar(self):
        label = generate_span_label(None, [], [])
        assert label == "Grammar"


class TestAnatomySuffix:
    def test_anatomy_appended_after_colon(self):
        label = generate_span_label("subject_verb_agreement", ["subject", "main_verb"], [])
        assert ":" in label
        assert "subject" in label

    def test_max_4_anatomy_elements(self):
        anatomy = ["subject", "prepositional_phrase", "main_verb", "antecedent", "appositive"]
        label = generate_span_label("subject_verb_agreement", anatomy, [])
        # Should contain at most 4 elements after ':'
        suffix = label.split(":", 1)[1] if ":" in label else ""
        parts = [p.strip() for p in suffix.split("+")]
        assert len(parts) <= 4

    def test_anatomy_key_with_no_human_label_skipped(self):
        # "predicate" has no entry in _ANATOMY_LABELS — should be omitted
        label = generate_span_label("subject_verb_agreement", ["predicate"], [])
        # Suffix should be absent (no recognisable labels → no suffix → just prefix)
        assert label == "SVA"

    def test_duplicate_anatomy_labels_deduplicated(self):
        # main_verb and verb_form both map to "verb blank"
        label = generate_span_label("subject_verb_agreement", ["main_verb", "verb_form"], [])
        assert label.count("verb blank") == 1


class TestTrapNotes:
    def test_trap_key_appended_in_brackets(self):
        label = generate_span_label(
            "subject_verb_agreement",
            ["subject"],
            ["nearest_noun_attraction"],
        )
        assert "[nearest noun attraction]" in label

    def test_non_trap_concept_key_not_in_brackets(self):
        label = generate_span_label(
            "subject_verb_agreement",
            [],
            ["subject_verb_agreement"],  # this is a concept, not a trap
        )
        assert "[" not in label

    def test_multiple_trap_notes_comma_separated(self):
        label = generate_span_label(
            "subject_verb_agreement",
            [],
            ["nearest_noun_attraction", "garden_path"],
        )
        assert "nearest noun attraction" in label
        assert "garden path" in label
        assert "[" in label


class TestTruncation:
    def test_output_never_exceeds_80_chars(self):
        long_anatomy = ["subject", "prepositional_phrase", "main_verb", "antecedent"]
        label = generate_span_label(
            "subject_verb_agreement",
            long_anatomy,
            ["nearest_noun_attraction", "garden_path", "modifier_attachment_ambiguity"],
        )
        assert len(label) <= 80

    def test_short_label_not_padded(self):
        label = generate_span_label("subject_verb_agreement", [], [])
        assert label == "SVA"
        assert len(label) < 80
