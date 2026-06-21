from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev"

    # Environment — set to "production" to enforce security checks at startup
    env: str = "development"

    # Auth
    admin_api_keys: str = "admin-key-change-me"
    student_api_keys: str = "student-key-change-me"

    # JWT Auth
    jwt_secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_max_concurrent: int = 8  # max parallel requests to Ollama (429 at ~20)
    annotation_max_concurrent: int = 1  # Ollama serializes GPU inference; >1 adds queue pressure with no throughput gain
    annotation_cache_prewarm_enabled: bool = True

    # Official test data
    official_test_verbal_dir: str = "../TESTS/DATA_SRC/2025-2026 Tests Answers/VERBAL"

    # Storage
    raw_asset_storage_backend: str = "local"
    local_archive_mirror: str = "./archive"
    object_storage_layout_config: str = "config/storage_layout.yaml"
    object_storage_backend: str = "local_fs"
    object_storage_local_root: str = "../local_object_store"

    # LLM defaults
    default_annotation_provider: str = "ollama"
    default_annotation_model: str = "deepseek-v4-pro:cloud"
    default_ollama_model: str = "deepseek-v4-pro:cloud"

    # Pass 3 span annotator — always uses Anthropic, never the default annotation provider
    span_annotator_model: str = "claude-sonnet-4-6"
    rules_version: str = "rules_agent_dsat_grammar_ingestion_generation_v8"
    official_auto_activate_for_testing: bool = False

    # Retry
    llm_retry_max_attempts: int = 3
    llm_retry_base_delay_s: float = 1.0
    llm_retry_max_delay_s: float = 30.0
    max_concurrent_jobs: int = 8
    # DB connection pool — sized so every concurrent job has a connection plus
    # headroom for request handlers. Keep pool_size >= max_concurrent_jobs.
    db_pool_size: int = 15
    db_max_overflow: int = 10
    # Hard ceiling for a single ingestion pipeline run; a slow/hung model is
    # aborted so it cannot occupy a job-semaphore slot indefinitely.
    pipeline_timeout_s: int = 10800  # 3 hours — covers 33-question annotation at ~3.9 min/call
    # Output token budget for Pass 1 extraction. A full 27-question module of
    # JSON exceeds 16K tokens for large modules; too low a cap truncates the
    # JSON mid-array and the parse fails.
    # For qwen3-vl cloud: cloud API may have lower limits than local models.
    extraction_max_tokens: int = 32000
    # Background sweeper interval — marks jobs stuck in in-progress statuses
    # longer than pipeline_timeout_s as failed. 0 disables the sweeper.
    job_sweeper_interval_s: int = 300

    # OCR / Vision — Option B: Ollama VLM (fused)
    ocr_vision_provider: str = "ollama"
    ocr_vision_model: str = "qwen3-vl:235b-instruct-cloud"
    ocr_strategy: str = "glm"  # glm | deepseek | ollama | anthropic | openai | auto
    ocr_fallback: bool = True
    ocr_allow_vlm_pdf_fallback: bool = False
    # PDF OCR is pagewise. This bounds concurrent page OCR calls; values above 3
    # are clamped in the ingest pipeline to avoid overloading local vision models.
    ocr_page_concurrency: int = 1
    vision_max_images: int = 10

    # OCR — Option A: DeepSeek OCR-2 (optional local server via vLLM Docker or LMDeploy)
    deepseek_ocr_base_url: str = ""
    deepseek_ocr_model: str = "deepseek-ai/DeepSeek-OCR-2"

    # OCR — Option G: GLM-OCR via Ollama (two-step: OCR then extraction LLM)
    glm_ocr_model: str = "glm-ocr:latest"

    # Layout detection — uses GLM-OCR to identify question/table/chart/figure regions
    layout_detection_enabled: bool = True

    # CORS — comma-separated list of allowed origins, or "*" to allow all
    cors_allowed_origins: str = "*"

    # Generation batches (Phase 1)
    generation_max_batch_size: int = 25
    generation_default_batch_size: int = 5
    generation_max_pending_batches: int = 20
    generation_batch_idempotency_ttl_hours: int = 24
    # Generation job retry limit (Phase 2) — transient failures only
    generation_job_max_retries: int = 3

    # Review swarm thresholds (Phase 3) — all scores 0-10
    generation_min_realism_score: float = 7.0
    generation_min_sat_fidelity_score: float = 7.0
    generation_min_distractor_quality_score: float = 6.5
    generation_min_taxonomy_match_score: float = 7.5
    generation_max_copy_risk_score: float = 5.0
    generation_max_reviewer_disagreement: float = 1.5
    # Review swarm composition (Phase 4 runner will use these)
    generation_review_providers: str = "openai,anthropic,ollama"
    generation_review_openai_model: str = "gpt-4o"
    generation_review_anthropic_model: str = "claude-sonnet-4-6"
    generation_review_ollama_model: str = "deepseek-v4-pro:cloud"
    generation_review_max_concurrent: int = 6
    generation_review_max_retries: int = 2

    # Student retrieval (Phase 7)
    inventory_sufficient_threshold: int = 5
    self_study_resurface_days: int = 30

    # Self-study agent (Phase 8)
    self_study_lookback_days: int = 30
    self_study_recency_half_life_days: int = 14
    self_study_top_k: int = 5
    self_study_min_attempts_per_target: int = 3
    self_study_min_gen_batch_size: int = 3
    self_study_target_cooldown_hours: int = 24
    self_study_gen_per_student_per_day: int = 20
    self_study_max_pending_per_target: int = 10
    self_study_max_pending_batches_per_student: int = 3
    self_study_poor_quality_cooldown_hours: int = 24

    # Controlled auto-release (Phase 10) — disabled by default until calibration data exists
    # Set generation_auto_release_enabled=true AND populate generation_auto_release_allowed_targets
    # before enabling. Both gates must pass.
    generation_auto_release_enabled: bool = False
    # Minimum number of previously admin-approved questions generated by the same
    # provider/model before that model is considered "proven" for auto-release.
    generation_auto_release_min_reviews: int = 3
    # Minimum historical acceptance rate (approved / total reviewed) for the
    # generator model over its lifetime of admin decisions.
    generation_auto_release_min_accept_rate: float = 0.80
    # JSON-encoded list of allowed target specs, each with optional keys:
    # domain, grammar_focus_key, reading_focus_key, difficulty_overall.
    # Empty string disables all targets even if the global flag is true.
    # Example: '[{"domain":"grammar","grammar_focus_key":"comma_splice"}]'
    generation_auto_release_allowed_targets: str = ""

    # Logging
    log_level: str = "INFO"
    log_json: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def admin_api_key_list(self) -> List[str]:
        return [k.strip() for k in self.admin_api_keys.split(",") if k.strip()]

    @property
    def student_api_key_list(self) -> List[str]:
        return [k.strip() for k in self.student_api_keys.split(",") if k.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
