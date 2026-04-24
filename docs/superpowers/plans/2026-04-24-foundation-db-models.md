# Foundation + DB + Models Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the DSAT backend from scratch with a FastAPI app, async Postgres connection, Alembic migrations, 10-table SQLAlchemy ORM, Pydantic schemas, API key auth, and V3 ontology constants.

**Architecture:** Single FastAPI service. asyncpg for Postgres, SQLAlchemy 2.0 async ORM, Alembic for migrations, Pydantic v2 for validation. Flat router structure grouped by domain.

**Tech Stack:** Python 3.12, FastAPI, asyncpg, SQLAlchemy 2.0 async, Alembic, Pydantic v2, pydantic-settings, uv

**Reference spec:** `docs/superpowers/specs/2026-04-24-segment-a-backend-rebuild-design.md`

---

## File Map

```
backend/
├── pyproject.toml                    # Project config, dependencies
├── .python-version                   # 3.12
├── .env.example                      # Template env vars
├── .gitignore                        # Python + env ignores
├── alembic.ini                       # Alembic config
├── migrations/
│   ├── env.py                        # Alembic env (async)
│   ├── script.py.mako                # Migration template
│   └── versions/
│       └── 001_initial_schema.py     # All 10 tables
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app + lifespan
│   ├── config.py                     # pydantic-settings
│   ├── database.py                   # asyncpg pool + SQLAlchemy engine
│   ├── auth.py                       # API key dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py                     # SQLAlchemy ORM (10 tables)
│   │   ├── ontology.py               # V3 allowed keys, enums, constants
│   │   ├── extract.py                # Pass 1 Pydantic schema
│   │   ├── annotation.py            # Pass 2 Pydantic schema
│   │   ├── payload.py               # HTTP request/response models
│   │   └── options.py               # Per-option Pydantic schema
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py                # GET / for health check
│   ├── llm/                          # Empty stubs (next plan)
│   │   └── __init__.py
│   ├── parsers/                      # Empty stubs (next plan)
│   │   └── __init__.py
│   ├── prompts/                      # Empty stubs (next plan)
│   │   └── __init__.py
│   ├── pipeline/                      # Empty stubs (next plan)
│   │   └── __init__.py
│   └── storage/
│       ├── __init__.py
│       └── local_store.py            # Local filesystem asset storage
└── tests/
    ├── conftest.py                    # Shared fixtures (async client, test DB)
    ├── test_health.py                 # Health endpoint test
    ├── test_models.py                 # ORM model tests
    ├── test_schemas.py                # Pydantic schema validation tests
    └── test_auth.py                   # API key auth tests
```

---

## Chunk 1: Project Scaffolding

### Task 1: Wipe old backend and create project structure

**Files:**
- Delete: `backend/main.py`, `backend/models.py`, `backend/schemas.py`, `backend/database.py`
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`
- Create: `backend/.env.example`
- Create: `backend/.gitignore`
- Create: `backend/app/__init__.py`

- [ ] **Step 1: Remove old backend files**

```bash
rm backend/main.py backend/models.py backend/schemas.py backend/database.py
```

- [ ] **Step 2: Create `.python-version`**

```
3.12
```

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[project]
name = "dsat-backend"
version = "0.1.0"
description = "DSAT question corpus ingestion, annotation, generation, and practice API"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-multipart>=0.0.18",
    "anthropic>=0.40",
    "openai>=1.50",
    "httpx>=0.28",
    "pymupdf>=1.25",
    "pillow>=11.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx",  # for TestClient
    "aiosqlite>=0.20",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 4: Create `.env.example`**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://dsat:dsat@localhost:5432/dsat

# Auth
ADMIN_API_KEYS=admin-key-change-me
STUDENT_API_KEYS=student-key-change-me

# LLM
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

# Storage
RAW_ASSET_STORAGE_BACKEND=local
LOCAL_ARCHIVE_MIRROR=./archive

# LLM defaults
DEFAULT_ANNOTATION_PROVIDER=anthropic
DEFAULT_ANNOTATION_MODEL=claude-sonnet-4-6
RULES_VERSION=rules_agent_dsat_grammar_ingestion_generation_v3
```

- [ ] **Step 5: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
*.db
archive/
.venv/
```

- [ ] **Step 6: Create `app/__init__.py`**

Empty file.

- [ ] **Step 7: Create venv and install dependencies**

```bash
cd backend && uv venv --python 3.12 && source .venv/bin/activate && uv pip install -e ".[dev]"
```

- [ ] **Step 8: Commit**

```bash
git add -A backend/ && git commit -m "feat: scaffold new backend project structure with pyproject.toml"
```

---

### Task 2: Create config module

**Files:**
- Create: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
import pytest

def test_settings_loads_from_env():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/testdb"
    os.environ["ADMIN_API_KEYS"] = "key1,key2"
    os.environ["STUDENT_API_KEYS"] = "skey1"
    from app.config import Settings
    s = Settings()
    assert "key1" in s.admin_api_keys
    assert s.database_url == "postgresql+asyncpg://test:test@localhost:5432/testdb"

def test_settings_default_values():
    os.environ.pop("ADMIN_API_KEYS", None)
    os.environ.pop("STUDENT_API_KEYS", None)
    from app.config import Settings
    s = Settings()
    assert s.default_annotation_provider == "anthropic"
    assert s.rules_version.startswith("rules_agent")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_config.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: Write implementation**

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://dsat:dsat@localhost:5432/dsat"

    # Auth
    admin_api_keys: str = "admin-key-change-me"
    student_api_keys: str = "student-key-change-me"

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # Storage
    raw_asset_storage_backend: str = "local"
    local_archive_mirror: str = "./archive"

    # LLM defaults
    default_annotation_provider: str = "anthropic"
    default_annotation_model: str = "claude-sonnet-4-6"
    rules_version: str = "rules_agent_dsat_grammar_ingestion_generation_v3"

    @property
    def admin_api_key_list(self) -> List[str]:
        return [k.strip() for k in self.admin_api_keys.split(",") if k.strip()]

    @property
    def student_api_key_list(self) -> List[str]:
        return [k.strip() for k in self.student_api_keys.split(",") if k.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config.py && git commit -m "feat: add pydantic-settings config module"
```

---

### Task 3: Create database module

**Files:**
- Create: `backend/app/database.py`
- Test: `backend/tests/test_database.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_database.py
import pytest

def test_database_module_imports():
    from app.database import engine, async_session, Base
    assert engine is not None
    assert async_session is not None
    assert Base is not None

@pytest.mark.asyncio
async def test_can_create_and_drop_tables():
    from app.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_database.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, pool_size=5, max_overflow=10)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_database.py -v
```

Expected: PASS (requires running Postgres — will use SQLite for test in conftest)

Note: The test above assumes Postgres is running. We'll add a SQLite test override in conftest.py (Task 7).

- [ ] **Step 5: Commit**

```bash
git add backend/app/database.py backend/tests/test_database.py && git commit -m "feat: add async database module with SQLAlchemy engine"
```

---

## Chunk 2: ORM Models + Ontology

### Task 4: Create ontology constants

**Files:**
- Create: `backend/app/models/ontology.py`
- Test: `backend/tests/test_ontology.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ontology.py
from app.models.ontology import (
    CONTENT_ORIGINS, JOB_TYPES, JOB_STATUSES, PRACTICE_STATUSES,
    OVERLAP_STATUSES, RELATION_TYPES, ASSET_TYPES, CHANGE_SOURCES,
    GRAMMAR_ROLE_KEYS, GRAMMAR_FOCUS_KEYS, SYNTACTIC_TRAP_KEYS,
    STIMULUS_MODE_KEYS, STEM_TYPE_KEYS, DISTRACTOR_TYPE_KEYS,
    PLANSIBILITY_SOURCE_KEYS, ANSWER_MECHANISM_KEYS, SOLVER_PATTERN_KEYS,
)

def test_content_origins():
    assert set(CONTENT_ORIGINS) == {"official", "unofficial", "generated"}

def test_job_statuses():
    assert "pending" in JOB_STATUSES
    assert "failed" in JOB_STATUSES
    assert "approved" in JOB_STATUSES

def test_grammar_role_keys():
    assert "sentence_boundary" in GRAMMAR_ROLE_KEYS
    assert "agreement" in GRAMMAR_ROLE_KEYS
    assert "expression_of_ideas" in GRAMMAR_ROLE_KEYS

def test_grammar_focus_by_role():
    from app.models.ontology import GRAMMAR_FOCUS_BY_ROLE
    assert "subject_verb_agreement" in GRAMMAR_FOCUS_BY_ROLE["agreement"]
    assert "punctuation_comma" in GRAMMAR_FOCUS_BY_ROLE["punctuation"]

def test_syntactic_trap_keys():
    assert "nearest_noun_attraction" in SYNTACTIC_TRAP_KEYS
    assert "none" in SYNTACTIC_TRAP_KEYS
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_ontology.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/models/ontology.py
"""V3 allowed keys, enums, and constants.
Source: rules_agent_dsat_grammar_ingestion_generation_v3.md
"""

# --- Content origin ---
CONTENT_ORIGINS = ("official", "unofficial", "generated")

# --- Job types ---
JOB_TYPES = ("ingest", "generate", "reannotate", "overlap_check")

# --- Job statuses (state machine) ---
JOB_STATUSES = (
    "pending", "parsing", "extracting", "generating",
    "annotating", "overlap_checking", "validating",
    "approved", "needs_review", "failed",
)

# --- Practice status ---
PRACTICE_STATUSES = ("draft", "active", "retired")

# --- Overlap status ---
OVERLAP_STATUSES = ("none", "possible", "confirmed")

# --- Relation types ---
RELATION_TYPES = (
    "overlaps_official", "derived_from", "near_duplicate",
    "generated_from", "adapted_from",
)

# --- Asset types ---
ASSET_TYPES = ("pdf", "image", "screenshot", "markdown", "json", "text")

# --- Change sources ---
CHANGE_SOURCES = ("ingest", "generate", "admin_edit", "reprocess")

# --- V3 §3.1 stimulus_mode_key ---
STIMULUS_MODE_KEYS = (
    "sentence_only", "passage_excerpt", "prose_single", "prose_paired",
    "prose_plus_table", "prose_plus_graph", "notes_bullets", "poem",
)

# --- V3 §3.2 stem_type_key ---
STEM_TYPE_KEYS = (
    "complete_the_text", "choose_main_idea", "choose_main_purpose",
    "choose_structure_description", "choose_sentence_function",
    "choose_likely_response", "choose_best_support", "choose_best_quote",
    "choose_best_completion_from_data", "choose_best_grammar_revision",
    "choose_best_transition", "choose_best_notes_synthesis",
)

# --- V3 §5 grammar_role_key ---
GRAMMAR_ROLE_KEYS = (
    "sentence_boundary", "agreement", "verb_form", "modifier",
    "punctuation", "parallel_structure", "pronoun", "expression_of_ideas",
)

# --- V3 §6 grammar_focus_key (grouped by role) ---
GRAMMAR_FOCUS_BY_ROLE = {
    "sentence_boundary": (
        "sentence_fragment", "comma_splice", "run_on_sentence", "sentence_boundary",
    ),
    "agreement": (
        "subject_verb_agreement", "pronoun_antecedent_agreement",
        "noun_countability", "determiners_articles", "affirmative_agreement",
    ),
    "verb_form": (
        "verb_tense_consistency", "verb_form", "voice_active_passive", "negation",
    ),
    "modifier": (
        "modifier_placement", "comparative_structures",
        "logical_predication", "relative_pronouns",
    ),
    "punctuation": (
        "punctuation_comma", "colon_dash_use", "semicolon_use",
        "conjunctive_adverb_usage", "apostrophe_use", "possessive_contraction",
        "appositive_punctuation", "hyphen_usage", "quotation_punctuation",
    ),
    "parallel_structure": (
        "parallel_structure", "elliptical_constructions", "conjunction_usage",
    ),
    "pronoun": (
        "pronoun_case", "pronoun_clarity", "pronoun_antecedent_agreement",
    ),
    "expression_of_ideas": (
        "redundancy_concision", "precision_word_choice",
        "register_style_consistency", "logical_relationships",
        "emphasis_meaning_shifts", "data_interpretation_claims",
        "transition_logic",
    ),
}

# Flat set of all grammar focus keys
GRAMMAR_FOCUS_KEYS = tuple(
    k for keys in GRAMMAR_FOCUS_BY_ROLE.values() for k in keys
)

# --- V3 §9 syntactic_trap_key ---
SYNTACTIC_TRAP_KEYS = (
    "none", "nearest_noun_attraction", "garden_path",
    "early_clause_anchor", "nominalization_obscures_subject",
    "interruption_breaks_subject_verb", "long_distance_dependency",
    "pronoun_ambiguity", "scope_of_negation",
    "modifier_attachment_ambiguity", "presupposition_trap",
    "temporal_sequence_ambiguity", "multiple",
)

# --- V3 §10.2 distractor_type_key ---
DISTRACTOR_TYPE_KEYS = (
    "semantic_imprecision", "logical_mismatch", "scope_error",
    "tone_mismatch", "grammar_error", "punctuation_error",
    "transition_mismatch", "data_misread", "goal_mismatch",
    "partially_supported", "overstatement", "understatement",
    "rhetorical_irrelevance", "correct",
)

# --- V3 §10.3 plausibility_source_key ---
PLANSIBILITY_SOURCE_KEYS = (
    "nearest_noun_attraction", "punctuation_style_bias",
    "auditory_similarity", "grammar_fit_only",
    "formal_register_match", "common_idiom_pull", "none",
)

# --- V3 §3.3 answer_mechanism_key ---
ANSWER_MECHANISM_KEYS = (
    "rule_application", "pattern_matching",
    "evidence_location", "inference", "data_synthesis",
)

# --- V3 §3.3 solver_pattern_key ---
SOLVER_PATTERN_KEYS = (
    "apply_grammar_rule_directly", "locate_error_zone",
    "compare_register", "evaluate_transition",
    "synthesize_notes", "eliminate_by_boundary",
)

# --- V3 §21.3 student_failure_mode_key ---
STUDENT_FAILURE_MODE_KEYS = (
    "nearest_noun_reflex", "comma_fix_illusion", "formal_word_bias",
    "longer_answer_bias", "punctuation_intimidation",
    "surface_similarity_bias", "scope_blindness",
    "modifier_hitchhike", "chronological_assumption",
    "extreme_word_trap", "overreading", "underreading",
    "grammar_fit_only", "register_confusion",
    "pronoun_anchor_error", "parallel_shape_bias",
    "transition_assumption", "idiom_memory_pull",
    "false_precision",
)

# --- V3 §21.2 distractor_distance ---
DISTRACTOR_DISTANCE_KEYS = ("wide", "moderate", "tight")

# --- V3 §3.3 difficulty keys ---
DIFFICULTY_KEYS = ("low", "medium", "high")

# --- V3 §3.3 frequency bands ---
FREQUENCY_BANDS = ("very_high", "high", "medium", "low", "very_low")

# --- V3 §17.6 tense register keys ---
TENSE_REGISTER_KEYS = (
    "narrative_past", "scientific_general_present",
    "historical_past", "study_procedure_past",
    "established_finding_present", "mixed_with_explicit_shift",
)

# --- V3 §22 passage_architecture_key ---
PASSAGE_ARCHITECTURE_KEYS = (
    "science_setup_finding_implication", "science_hypothesis_method_result",
    "history_claim_evidence_limitation", "history_assumption_revision",
    "literature_observation_interpretation_shift",
    "literature_character_conflict_reveal",
    "economics_theory_exception_example",
    "economics_problem_solution_tradeoff",
    "rhetoric_claim_counterclaim_resolution",
    "notes_fact_selection_contrast",
)

# --- question_family_key ---
QUESTION_FAMILY_KEYS = (
    "conventions_grammar", "expression_of_ideas",
    "craft_and_structure", "information_and_ideas",
)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_ontology.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/ontology.py backend/tests/test_ontology.py && git commit -m "feat: add V3 ontology constants (grammar keys, enums, controlled vocabularies)"
```

---

### Task 5: Create SQLAlchemy ORM models (10 tables)

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/db.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
import pytest
from sqlalchemy import inspect

def test_all_ten_tables_exist():
    from app.models.db import Base
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "question_jobs", "questions", "question_versions",
        "question_annotations", "question_options", "question_assets",
        "question_relations", "llm_evaluations", "users", "user_progress",
    }
    assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"

def test_question_jobs_columns():
    from app.models.db import QuestionJob
    mapper = inspect(QuestionJob).mapper
    col_names = {c.key for c in mapper.columns}
    required = {"id", "job_type", "content_origin", "input_format", "status",
                "provider_name", "model_name", "prompt_version", "rules_version",
                "pass1_json", "pass2_json", "validation_errors_jsonb",
                "comparison_group_id", "created_at", "updated_at"}
    assert required.issubset(col_names), f"Missing cols: {required - col_names}"

def test_questions_columns():
    from app.models.db import Question
    mapper = inspect(Question).mapper
    col_names = {c.key for c in mapper.columns}
    required = {"id", "content_origin", "source_exam_code", "source_module_code",
                "stimulus_mode_key", "stem_type_key",
                "current_question_text", "current_passage_text",
                "current_correct_option_label", "current_explanation_text",
                "practice_status", "official_overlap_status",
                "is_admin_edited", "metadata_managed_by_llm",
                "created_at", "updated_at"}
    assert required.issubset(col_names), f"Missing cols: {required - col_names}"

def test_question_options_columns():
    from app.models.db import QuestionOption
    mapper = inspect(QuestionOption).mapper
    col_names = {c.key for c in mapper.columns}
    required = {"id", "question_id", "option_label", "option_text",
                "is_correct", "option_role", "distractor_type_key",
                "precision_score", "created_at"}
    assert required.issubset(col_names), f"Missing cols: {required - col_names}"

def test_foreign_keys():
    from app.models.db import UserProgress
    mapper = inspect(UserProgress).mapper
    fk_cols = {c.key for c in mapper.columns if c.foreign_keys}
    assert "user_id" in fk_cols
    assert "question_id" in fk_cols
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_models.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/models/__init__.py
```

```python
# app/models/db.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, SmallInteger, Float, Boolean, Text,
    ForeignKey, DateTime, Enum, JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base
from app.models.ontology import (
    CONTENT_ORIGINS, JOB_TYPES, JOB_STATUSES, PRACTICE_STATUSES,
    OVERLAP_STATUSES, RELATION_TYPES, ASSET_TYPES, CHANGE_SOURCES,
    DISTRACTOR_TYPE_KEYS,
)

def _utcnow():
    return datetime.now(timezone.utc)


class QuestionJob(Base):
    __tablename__ = "question_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(Enum(*JOB_TYPES, name="job_type_enum"), nullable=False)
    content_origin = Column(Enum(*CONTENT_ORIGINS, name="content_origin_enum"), nullable=False)
    input_format = Column(String(20), nullable=False)
    status = Column(Enum(*JOB_STATUSES, name="job_status_enum"), nullable=False, default="pending")
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    prompt_version = Column(String(20), nullable=False, default="v3.0")
    rules_version = Column(String(100), nullable=False)
    raw_asset_id = Column(UUID(as_uuid=True), ForeignKey("question_assets.id"), nullable=True)
    pass1_json = Column(JSONB, nullable=True)
    pass2_json = Column(JSONB, nullable=True)
    validation_errors_jsonb = Column(JSONB, nullable=True)
    comparison_group_id = Column(UUID(as_uuid=True), nullable=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    question = relationship("Question", back_populates="jobs", foreign_keys=[question_id])


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_origin = Column(Enum(*CONTENT_ORIGINS, name="content_origin_enum2"), nullable=False)
    source_exam_code = Column(String(20), nullable=True)
    source_module_code = Column(String(10), nullable=True)
    source_question_number = Column(Integer, nullable=True)
    stimulus_mode_key = Column(String(30), nullable=True)
    stem_type_key = Column(String(40), nullable=True)
    current_question_text = Column(Text, nullable=False)
    current_passage_text = Column(Text, nullable=True)
    current_correct_option_label = Column(String(1), nullable=False)
    current_explanation_text = Column(Text, nullable=True)
    practice_status = Column(Enum(*PRACTICE_STATUSES, name="practice_status_enum"), nullable=False, default="draft")
    official_overlap_status = Column(Enum(*OVERLAP_STATUSES, name="overlap_status_enum"), nullable=False, default="none")
    canonical_official_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    derived_from_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    generation_source_set = Column(JSONB, nullable=True)
    is_admin_edited = Column(Boolean, nullable=False, default=False)
    metadata_managed_by_llm = Column(Boolean, nullable=False, default=True)
    latest_annotation_id = Column(UUID(as_uuid=True), ForeignKey("question_annotations.id"), nullable=True)
    latest_version_id = Column(UUID(as_uuid=True), ForeignKey("question_versions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    jobs = relationship("QuestionJob", back_populates="question", foreign_keys="[QuestionJob.question_id]")
    versions = relationship("QuestionVersion", back_populates="question", order_by="QuestionVersion.version_number")
    annotations = relationship("QuestionAnnotation", back_populates="question")
    options = relationship("QuestionOption", back_populates="question", order_by="QuestionOption.option_label")
    assets = relationship("QuestionAsset", back_populates="question")
    outgoing_relations = relationship("QuestionRelation", back_populates="from_question", foreign_keys="[QuestionRelation.from_question_id]")
    incoming_relations = relationship("QuestionRelation", back_populates="to_question", foreign_keys="[QuestionRelation.to_question_id]")
    progress_records = relationship("UserProgress", back_populates="question")


class QuestionVersion(Base):
    __tablename__ = "question_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    change_source = Column(Enum(*CHANGE_SOURCES, name="change_source_enum"), nullable=False)
    question_text = Column(Text, nullable=False)
    passage_text = Column(Text, nullable=True)
    choices_jsonb = Column(JSONB, nullable=False)
    correct_option_label = Column(String(1), nullable=False)
    explanation_text = Column(Text, nullable=True)
    editor_user_id = Column(String(50), nullable=True)
    change_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="versions")


class QuestionAnnotation(Base):
    __tablename__ = "question_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    question_version_id = Column(UUID(as_uuid=True), ForeignKey("question_versions.id"), nullable=False)
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    prompt_version = Column(String(20), nullable=False)
    rules_version = Column(String(100), nullable=False)
    annotation_jsonb = Column(JSONB, nullable=False, default=dict)
    explanation_jsonb = Column(JSONB, nullable=False, default=dict)
    generation_profile_jsonb = Column(JSONB, nullable=True)
    confidence_jsonb = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="annotations", foreign_keys=[question_id])


class QuestionOption(Base):
    __tablename__ = "question_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    question_version_id = Column(UUID(as_uuid=True), ForeignKey("question_versions.id"), nullable=False)
    option_label = Column(String(1), nullable=False)
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    option_role = Column(String(10), nullable=False)
    distractor_type_key = Column(String(30), nullable=True)
    semantic_relation_key = Column(String(40), nullable=True)
    plausibility_source_key = Column(String(30), nullable=True)
    option_error_focus_key = Column(String(40), nullable=True)
    why_plausible = Column(Text, nullable=True)
    why_wrong = Column(Text, nullable=True)
    grammar_fit = Column(String(3), nullable=True)
    tone_match = Column(String(3), nullable=True)
    precision_score = Column(SmallInteger, nullable=True)
    student_failure_mode_key = Column(String(30), nullable=True)
    distractor_distance = Column(String(10), nullable=True)
    distractor_competition_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="options")


class QuestionAsset(Base):
    __tablename__ = "question_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    content_origin = Column(Enum(*CONTENT_ORIGINS, name="content_origin_enum3"), nullable=False)
    asset_type = Column(Enum(*ASSET_TYPES, name="asset_type_enum"), nullable=False)
    storage_path = Column(Text, nullable=False)
    mime_type = Column(String(100), nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    source_url = Column(Text, nullable=True)
    source_name = Column(String(200), nullable=True)
    source_exam_code = Column(String(20), nullable=True)
    source_module_code = Column(String(10), nullable=True)
    source_question_number = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    question = relationship("Question", back_populates="assets")


class QuestionRelation(Base):
    __tablename__ = "question_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    to_question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    relation_type = Column(Enum(*RELATION_TYPES, name="relation_type_enum"), nullable=False)
    relation_strength = Column(Float, nullable=True)
    detection_method = Column(String(30), nullable=True)
    is_human_confirmed = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    from_question = relationship("Question", back_populates="outgoing_relations", foreign_keys=[from_question_id])
    to_question = relationship("Question", back_populates="incoming_relations", foreign_keys=[to_question_id])


class LlmEvaluation(Base):
    __tablename__ = "llm_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("question_jobs.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=True)
    provider_name = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    task_type = Column(String(20), nullable=False)
    score_overall = Column(Float, nullable=True)
    score_metadata = Column(Float, nullable=True)
    score_explanation = Column(Float, nullable=True)
    score_generation = Column(Float, nullable=True)
    review_notes = Column(Text, nullable=True)
    recommended_for_default = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


# --- Segment B tables ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    progress_records = relationship("UserProgress", back_populates="user")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    selected_option_label = Column(String(1), nullable=False)
    missed_grammar_focus_key = Column(String(50), nullable=True)
    missed_syntactic_trap_key = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="progress_records")
    question = relationship("Question", back_populates="progress_records")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_models.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/ backend/tests/test_models.py && git commit -m "feat: add SQLAlchemy ORM models for all 10 tables"
```

---

### Task 6: Create Pydantic schemas (extract, annotation, options, payload)

**Files:**
- Create: `backend/app/models/extract.py`
- Create: `backend/app/models/annotation.py`
- Create: `backend/app/models/options.py`
- Create: `backend/app/models/payload.py`
- Test: `backend/tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schemas.py
import pytest
from pydantic import ValidationError

def test_question_extract_valid():
    from app.models.extract import QuestionExtract
    data = {
        "question_text": "Which choice completes the text?",
        "passage_text": "The colony of corals ______ an important role.",
        "options": [
            {"label": "A", "text": "play"},
            {"label": "B", "text": "have played"},
            {"label": "C", "text": "plays"},
            {"label": "D", "text": "is playing"},
        ],
        "correct_option_label": "C",
        "source_exam_code": "PT4",
        "source_module_code": "M1",
        "source_question_number": 1,
    }
    q = QuestionExtract(**data)
    assert q.correct_option_label == "C"
    assert len(q.options) == 4

def test_question_extract_rejects_bad_label():
    from app.models.extract import QuestionExtract
    with pytest.raises(ValidationError):
        QuestionExtract(
            question_text="test",
            options=[{"label": "E", "text": "bad"}],
            correct_option_label": "E",
        )

def test_question_annotation_valid():
    from app.models.annotation import QuestionAnnotation
    data = {
        "grammar_role_key": "agreement",
        "grammar_focus_key": "subject_verb_agreement",
        "syntactic_trap_key": "nearest_noun_attraction",
        "difficulty_overall": "medium",
        "explanation_short": "Singular subject requires singular verb.",
        "explanation_full": "The grammatical subject is the singular noun colony.",
        "annotation_confidence": 0.95,
        "needs_human_review": False,
    }
    a = QuestionAnnotation(**data)
    assert a.grammar_focus_key == "subject_verb_agreement"

def test_question_annotation_rejects_bad_focus():
    from app.models.annotation import QuestionAnnotation
    with pytest.raises(ValidationError):
        QuestionAnnotation(
            grammar_role_key="agreement",
            grammar_focus_key="not_a_real_key",
            syntactic_trap_key="none",
            difficulty_overall="medium",
            explanation_short="test",
            explanation_full="test",
            annotation_confidence=0.5,
            needs_human_review=False,
        )

def test_option_schema_valid():
    from app.models.options import OptionAnalysis
    data = {
        "option_label": "A",
        "option_text": "play",
        "is_correct": False,
        "option_role": "distractor",
        "distractor_type_key": "grammar_error",
        "why_plausible": "Nearest noun attraction",
        "why_wrong": "Subject is singular",
        "grammar_fit": "no",
        "tone_match": "yes",
        "precision_score": 1,
    }
    o = OptionAnalysis(**data)
    assert o.precision_score == 1

def test_question_recall_response():
    from app.models.payload import QuestionRecallResponse
    data = {
        "id": "00000000-0000-0000-0000-000000000001",
        "content_origin": "official",
        "current_question_text": "Which choice completes the text?",
        "current_passage_text": "A passage here.",
        "current_correct_option_label": "C",
        "practice_status": "active",
        "grammar_role_key": "agreement",
        "grammar_focus_key": "subject_verb_agreement",
        "difficulty_overall": "medium",
    }
    r = QuestionRecallResponse(**data)
    assert r.practice_status == "active"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_schemas.py -v
```

Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# app/models/extract.py
"""Pass 1 Pydantic schema — Question extraction output."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from app.models.ontology import STIMULUS_MODE_KEYS, STEM_TYPE_KEYS


class ExtractedOption(BaseModel):
    label: str = Field(pattern=r"^[A-D]$")
    text: str


class QuestionExtract(BaseModel):
    question_text: str
    passage_text: Optional[str] = None
    paired_passage_text: Optional[str] = None
    options: List[ExtractedOption] = Field(min_length=4, max_length=4)
    correct_option_label: str = Field(pattern=r"^[A-D]$")
    source_exam_code: Optional[str] = None
    source_module_code: Optional[str] = None
    source_question_number: Optional[int] = None
    stimulus_mode_key: Optional[str] = None
    stem_type_key: Optional[str] = None
    table_data: Optional[dict] = None
    graph_data: Optional[dict] = None

    @field_validator("stimulus_mode_key")
    @classmethod
    def validate_stimulus(cls, v):
        if v and v not in STIMULUS_MODE_KEYS:
            raise ValueError(f"Invalid stimulus_mode_key: {v}")
        return v

    @field_validator("stem_type_key")
    @classmethod
    def validate_stem(cls, v):
        if v and v not in STEM_TYPE_KEYS:
            raise ValueError(f"Invalid stem_type_key: {v}")
        return v
```

```python
# app/models/annotation.py
"""Pass 2 Pydantic schema — Question annotation output."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from app.models.ontology import (
    GRAMMAR_ROLE_KEYS, GRAMMAR_FOCUS_KEYS, GRAMMAR_FOCUS_BY_ROLE,
    SYNTACTIC_TRAP_KEYS, DIFFICULTY_KEYS, FREQUENCY_BANDS,
    STUDENT_FAILURE_MODE_KEYS, PASSAGE_ARCHITECTURE_KEYS,
    DISTRACTOR_DISTANCE_KEYS,
)


class QuestionAnnotation(BaseModel):
    # Classification
    grammar_role_key: Optional[str] = None
    grammar_focus_key: str
    secondary_grammar_focus_keys: List[str] = Field(default_factory=list)
    syntactic_trap_key: str = "none"
    difficulty_overall: str
    distractor_strength: Optional[str] = None
    question_family_key: Optional[str] = None
    topic_broad: Optional[str] = None
    topic_fine: Optional[str] = None
    disambiguation_rule_applied: Optional[str] = None
    classification_rationale: Optional[str] = None

    # Explanations
    explanation_short: str = Field(max_length=300)
    explanation_full: str = Field(max_length=2000)
    evidence_span_text: Optional[str] = None

    # Confidence / review
    annotation_confidence: float = Field(ge=0.0, le=1.0)
    needs_human_review: bool = False
    review_notes: Optional[str] = None

    # V3 §21-29 extensions (optional for MVP)
    distractor_distance: Optional[str] = None
    distractor_competition_score: Optional[float] = None
    plausible_wrong_count: Optional[int] = None
    answer_separation_strength: Optional[str] = None
    passage_architecture_key: Optional[str] = None
    official_similarity_score: Optional[float] = None
    structural_similarity_score: Optional[float] = None
    empirical_difficulty_estimate: Optional[float] = None

    @field_validator("grammar_focus_key")
    @classmethod
    def validate_focus_key(cls, v):
        if v not in GRAMMAR_FOCUS_KEYS:
            raise ValueError(f"Invalid grammar_focus_key: {v}")
        return v

    @field_validator("syntactic_trap_key")
    @classmethod
    def validate_trap_key(cls, v):
        if v not in SYNTACTIC_TRAP_KEYS:
            raise ValueError(f"Invalid syntactic_trap_key: {v}")
        return v

    @field_validator("difficulty_overall")
    @classmethod
    def validate_difficulty(cls, v):
        if v not in DIFFICULTY_KEYS:
            raise ValueError(f"Invalid difficulty: {v}")
        return v

    @field_validator("grammar_role_key")
    @classmethod
    def validate_role_key(cls, v):
        if v and v not in GRAMMAR_ROLE_KEYS:
            raise ValueError(f"Invalid grammar_role_key: {v}")
        return v

    @field_validator("distractor_distance")
    @classmethod
    def validate_distractor_distance(cls, v):
        if v and v not in DISTRACTOR_DISTANCE_KEYS:
            raise ValueError(f"Invalid distractor_distance: {v}")
        return v

    @field_validator("passage_architecture_key")
    @classmethod
    def validate_passage_arch(cls, v):
        if v and v not in PASSAGE_ARCHITECTURE_KEYS:
            raise ValueError(f"Invalid passage_architecture_key: {v}")
        return v
```

```python
# app/models/options.py
"""Per-option Pydantic schema — V3 §10 option-level analysis."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.models.ontology import (
    DISTRACTOR_TYPE_KEYS, PLANSIBILITY_SOURCE_KEYS,
    STUDENT_FAILURE_MODE_KEYS, DISTRACTOR_DISTANCE_KEYS,
)


class OptionAnalysis(BaseModel):
    option_label: str = Field(pattern=r"^[A-D]$")
    option_text: str
    is_correct: bool
    option_role: str  # "correct" or "distractor"
    distractor_type_key: Optional[str] = None
    semantic_relation_key: Optional[str] = None
    plausibility_source_key: Optional[str] = None
    option_error_focus_key: Optional[str] = None
    why_plausible: Optional[str] = None
    why_wrong: Optional[str] = None
    grammar_fit: Optional[str] = None  # "yes" or "no"
    tone_match: Optional[str] = None    # "yes" or "no"
    precision_score: Optional[int] = Field(default=None, ge=1, le=3)
    student_failure_mode_key: Optional[str] = None
    distractor_distance: Optional[str] = None
    distractor_competition_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("distractor_type_key")
    @classmethod
    def validate_distractor_type(cls, v):
        if v and v not in DISTRACTOR_TYPE_KEYS:
            raise ValueError(f"Invalid distractor_type_key: {v}")
        return v

    @field_validator("plausibility_source_key")
    @classmethod
    def validate_plausibility(cls, v):
        if v and v not in PLANSIBILITY_SOURCE_KEYS:
            raise ValueError(f"Invalid plausibility_source_key: {v}")
        return v

    @field_validator("student_failure_mode_key")
    @classmethod
    def validate_failure_mode(cls, v):
        if v and v not in STUDENT_FAILURE_MODE_KEYS:
            raise ValueError(f"Invalid student_failure_mode_key: {v}")
        return v

    @field_validator("distractor_distance")
    @classmethod
    def validate_distractor_distance(cls, v):
        if v and v not in DISTRACTOR_DISTANCE_KEYS:
            raise ValueError(f"Invalid distractor_distance: {v}")
        return v

    @field_validator("grammar_fit")
    @classmethod
    def validate_grammar_fit(cls, v):
        if v and v not in ("yes", "no"):
            raise ValueError("grammar_fit must be 'yes' or 'no'")
        return v

    @field_validator("tone_match")
    @classmethod
    def validate_tone_match(cls, v):
        if v and v not in ("yes", "no"):
            raise ValueError("tone_match must be 'yes' or 'no'")
        return v
```

```python
# app/models/payload.py
"""HTTP request/response models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class QuestionRecallResponse(BaseModel):
    id: str
    content_origin: str
    current_question_text: str
    current_passage_text: Optional[str] = None
    current_correct_option_label: str
    practice_status: str
    grammar_role_key: Optional[str] = None
    grammar_focus_key: Optional[str] = None
    difficulty_overall: Optional[str] = None
    stimulus_mode_key: Optional[str] = None
    source_exam_code: Optional[str] = None

    model_config = {"from_attributes": True}


class QuestionDetailResponse(BaseModel):
    id: str
    content_origin: str
    current_question_text: str
    current_passage_text: Optional[str] = None
    current_correct_option_label: str
    current_explanation_text: Optional[str] = None
    practice_status: str
    official_overlap_status: str
    is_admin_edited: bool
    source_exam_code: Optional[str] = None
    source_module_code: Optional[str] = None
    latest_annotation: Optional[dict] = None
    options: List[dict] = Field(default_factory=list)
    lineage: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserProgressCreate(BaseModel):
    user_id: int
    question_id: str
    is_correct: bool
    selected_option_label: str = Field(pattern=r"^[A-D]$")
    missed_grammar_focus_key: Optional[str] = None
    missed_syntactic_trap_key: Optional[str] = None


class UserStats(BaseModel):
    total_answered: int
    total_correct: int
    accuracy: float
    top_missed_focus_keys: List[str] = Field(default_factory=list)
    top_missed_trap_keys: List[str] = Field(default_factory=list)


class AdminEditRequest(BaseModel):
    question_text: Optional[str] = None
    passage_text: Optional[str] = None
    correct_option_label: Optional[str] = Field(default=None, pattern=r"^[A-D]$")
    explanation_text: Optional[str] = None
    change_notes: Optional[str] = None


class EvaluationScoreRequest(BaseModel):
    score_overall: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    score_metadata: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    score_explanation: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    score_generation: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    review_notes: Optional[str] = None
    recommended_for_default: Optional[bool] = None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_schemas.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/extract.py backend/app/models/annotation.py backend/app/models/options.py backend/app/models/payload.py backend/tests/test_schemas.py && git commit -m "feat: add Pydantic schemas for extract, annotation, options, and API payloads"
```

---

## Chunk 3: Auth, Main App, Alembic, and Health Endpoint

### Task 7: Create test conftest and auth module

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/app/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auth.py
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.auth import admin_required, student_required

app = FastAPI()

@app.get("/admin-test", dependencies=[Depends(admin_required)])
def admin_endpoint():
    return {"ok": True}

@app.get("/student-test", dependencies=[Depends(student_required)])
def student_endpoint():
    return {"ok": True}

client = TestClient(app)

def test_admin_with_valid_key():
    response = client.get("/admin-test", headers={"X-API-Key": "admin-test-key"})
    assert response.status_code == 200

def test_admin_with_invalid_key():
    response = client.get("/admin-test", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403

def test_admin_with_no_key():
    response = client.get("/admin-test")
    assert response.status_code == 403

def test_student_with_valid_key():
    response = client.get("/student-test", headers={"X-API-Key": "student-test-key"})
    assert response.status_code == 200

def test_student_with_admin_key():
    response = client.get("/student-test", headers={"X-API-Key": "admin-test-key"})
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && ADMIN_API_KEYS=admin-test-key STUDENT_API_KEYS=student-test-key pytest tests/test_auth.py -v
```

Expected: FAIL

- [ ] **Step 3: Write conftest**

```python
# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient

# Force test env before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://dsat:dsat@localhost:5432/dsat_test")
os.environ.setdefault("ADMIN_API_KEYS", "admin-test-key")
os.environ.setdefault("STUDENT_API_KEYS", "student-test-key")


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)
```

- [ ] **Step 4: Write auth module**

```python
# app/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def admin_required(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if api_key not in settings.admin_api_key_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin API key")
    return api_key


async def student_required(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if api_key not in settings.student_api_key_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid student API key")
    return api_key
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_auth.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/auth.py backend/tests/conftest.py backend/tests/test_auth.py && git commit -m "feat: add API key auth dependencies for admin and student endpoints"
```

---

### Task 8: Create main FastAPI app with lifespan and health router

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/health.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_health.py
def test_health_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_health.py -v
```

Expected: FAIL

- [ ] **Step 3: Write health router**

```python
# app/routers/__init__.py
```

```python
# app/routers/health.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 4: Write main app**

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB pool, LLM clients, etc.
    yield
    # Shutdown: close DB pool, etc.


app = FastAPI(title="DSAT Grammar API", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && source .venv/bin/activate && pytest tests/test_health.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/app/routers/ backend/tests/test_health.py && git commit -m "feat: add FastAPI app with lifespan and health endpoint"
```

---

### Task 9: Set up Alembic and create initial migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/001_initial_schema.py`

- [ ] **Step 1: Initialize Alembic**

```bash
cd backend && source .venv/bin/activate && alembic init migrations
```

- [ ] **Step 2: Configure `alembic.ini`**

Edit `alembic.ini` to set `sqlalchemy.url` to empty (we'll use env.py to get it from Settings):

```ini
sqlalchemy.url =
```

- [ ] **Step 3: Configure `migrations/env.py` for async**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.config import get_settings
from app.models.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Generate initial migration**

```bash
cd backend && source .venv/bin/activate && alembic revision --autogenerate -m "001_initial_schema"
```

- [ ] **Step 5: Start PostgreSQL and create database**

```bash
sudo service postgresql start
sudo -u postgres createdb dsat 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER dsat WITH PASSWORD 'dsat';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dsat TO dsat;"
```

- [ ] **Step 6: Run migration**

```bash
cd backend && source .venv/bin/activate && alembic upgrade head
```

Expected: All 10 tables created.

- [ ] **Step 7: Verify tables exist**

```bash
sudo -u postgres psql -d dsat -c "\dt"
```

Expected: 10 tables listed.

- [ ] **Step 8: Commit**

```bash
git add backend/alembic.ini backend/migrations/ && git commit -m "feat: add Alembic config and initial 10-table migration"
```

---

### Task 10: Create local storage module and empty stubs

**Files:**
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/local_store.py`
- Create: `backend/app/llm/__init__.py`
- Create: `backend/app/parsers/__init__.py`
- Create: `backend/app/prompts/__init__.py`
- Create: `backend/app/pipeline/__init__.py`

- [ ] **Step 1: Write local_store.py**

```python
# app/storage/local_store.py
"""Local filesystem asset storage.
Stores raw assets (PDFs, images, markdown) as files on disk.
Paths are recorded in question_assets.storage_path.
"""
import os
import hashlib
from pathlib import Path
from app.config import get_settings


def _archive_dir() -> Path:
    settings = get_settings()
    path = Path(settings.local_archive_mirror)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def save_asset(filename: str, content: bytes, subfolder: str = "") -> str:
    """Save a raw asset file to the local archive.
    Returns the storage path relative to the archive root.
    """
    archive = _archive_dir()
    if subfolder:
        target = archive / subfolder
    else:
        target = archive
    target.mkdir(parents=True, exist_ok=True)

    dest = target / filename
    dest.write_bytes(content)
    return str(dest)


async def read_asset(storage_path: str) -> bytes:
    """Read a raw asset from the local archive."""
    return Path(storage_path).read_bytes()


def compute_checksum(content: bytes) -> str:
    """SHA-256 checksum for deduplication."""
    return hashlib.sha256(content).hexdigest()
```

- [ ] **Step 2: Create empty `__init__.py` files for stub packages**

```bash
touch backend/app/storage/__init__.py backend/app/llm/__init__.py backend/app/parsers/__init__.py backend/app/prompts/__init__.py backend/app/pipeline/__init__.py
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/storage/ backend/app/llm/ backend/app/parsers/ backend/app/prompts/ backend/app/pipeline/ && git commit -m "feat: add local asset storage module and empty stub packages for LLM, parsers, prompts, pipeline"
```

---

### Task 11: Verify everything runs end-to-end

- [ ] **Step 1: Run all tests**

```bash
cd backend && source .venv/bin/activate && pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Start the FastAPI server**

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 3: Test health endpoint**

```bash
curl http://localhost:8000/
```

Expected: `{"status":"ok","version":"0.1.0"}`

- [ ] **Step 4: Test auth rejection**

```bash
curl -X GET http://localhost:8000/admin-test -H "X-API-Key: wrong" || echo "Auth works — 403 expected for now"
```

- [ ] **Step 5: Final commit**

```bash
git add -A backend/ && git commit -m "feat: complete foundation — FastAPI app, Postgres, ORM, schemas, auth, storage"
```

---

## Next Plans

1. **LLM Providers + Parsers** — Anthropic/OpenAI/Ollama providers, PDF/image/markdown/JSON parsers, prompt templates
2. **Pipeline + Routers** — Orchestrator, overlap detection, validator, ingestion/generation/recall/admin/student routers
3. **Integration Tests + Deployment** — End-to-end pipeline tests, Docker, Supabase storage swap