"""Schemas for approval-gated rule/vocabulary amendments."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AmendmentStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MANUAL_PATCH = "needs_manual_patch"
    MORE_EVIDENCE_REQUESTED = "more_evidence_requested"
    PROMOTED = "promoted"


class AffectedDoc(StrEnum):
    READING = "reading"
    GRAMMAR = "grammar"


class RuleDocPatch(BaseModel):
    """Patch proposed against the body of one rules document."""

    model_config = ConfigDict(extra="forbid")

    target_section: str = Field(..., min_length=1)
    before: str = Field(..., min_length=1)
    after: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class MasterJsonPatch(BaseModel):
    """Controlled-vocabulary change paired with a rule-doc amendment."""

    model_config = ConfigDict(extra="forbid")

    affected_vocab: str = Field(..., min_length=1)
    proposed_value: str = Field(..., min_length=1)
    parent_key: str | None = None
    description: str = ""


class SupportingExample(BaseModel):
    """Official-source evidence supporting the amendment."""

    model_config = ConfigDict(extra="forbid")

    source_job_id: str = Field(..., min_length=1)
    source_exam_code: str = Field(..., min_length=1)
    source_subject_code: str = Field(..., min_length=1)
    source_section_code: str = Field(..., min_length=1)
    source_module_code: str = Field(..., min_length=1)
    source_question_number: int = Field(..., ge=1)
    official_evidence: str = Field(..., min_length=1)


class AdminDecision(BaseModel):
    """Reviewer decision metadata."""

    model_config = ConfigDict(extra="forbid")

    reviewer: str = Field(..., min_length=1)
    decision: Literal["approve", "reject", "request_more_evidence", "promote"]
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""


class RuleAmendment(BaseModel):
    """Durable amendment file schema.

    Only official-source ingestion may create amendments. The amendment is the
    reviewable bridge between a rules-doc body patch and a later active
    controlled-vocabulary entry in ``vocabulary/master.json``.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    amendment_id: str = Field(..., min_length=1)
    status: AmendmentStatus = AmendmentStatus.PENDING
    source_job_id: str = Field(..., min_length=1)
    source_exam_code: str = Field(..., min_length=1)
    source_subject_code: str = Field(..., min_length=1)
    source_section_code: str = Field(..., min_length=1)
    source_module_code: str = Field(..., min_length=1)
    source_question_number: int = Field(..., ge=1)
    content_origin: Literal["official"]
    affected_doc: AffectedDoc
    proposal_type: str = Field(..., min_length=1)
    affected_vocab: str = Field(..., min_length=1)
    proposed_value: str = Field(..., min_length=1)
    parent_key: str | None = None
    definition: str = Field(..., min_length=1)
    current_best_fit: str = Field(..., min_length=1)
    why_current_rules_are_insufficient: str = Field(..., min_length=1)
    official_evidence: str = Field(..., min_length=1)
    rule_doc_patch: RuleDocPatch
    master_json_patch: MasterJsonPatch
    supporting_examples: list[SupportingExample] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
    admin_decision: AdminDecision | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("affected_vocab")
    @classmethod
    def affected_vocab_must_look_like_constant(cls, value: str) -> str:
        if value.upper() != value:
            raise ValueError("affected_vocab must be an ontology constant name")
        return value

    @model_validator(mode="after")
    def validate_patch_consistency(self) -> RuleAmendment:
        if self.master_json_patch.affected_vocab != self.affected_vocab:
            raise ValueError("master_json_patch.affected_vocab must match affected_vocab")
        if self.master_json_patch.proposed_value != self.proposed_value:
            raise ValueError("master_json_patch.proposed_value must match proposed_value")
        if self.master_json_patch.parent_key != self.parent_key:
            raise ValueError("master_json_patch.parent_key must match parent_key")
        if _is_hierarchical_vocab(self.affected_vocab) and not self.parent_key:
            raise ValueError("parent_key is required for hierarchical vocabularies")
        if self.supporting_examples:
            for example in self.supporting_examples:
                if example.source_job_id == self.source_job_id:
                    break
            else:
                raise ValueError("supporting_examples must include the source job")
        return self

    def to_file_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation for amendment files."""
        return self.model_dump(mode="json")


HIERARCHICAL_VOCABS = frozenset({
    "GRAMMAR_FOCUS_BY_ROLE",
    "READING_FOCUS_BY_SKILL_FAMILY",
})


def _is_hierarchical_vocab(vocab: str) -> bool:
    return vocab in HIERARCHICAL_VOCABS
