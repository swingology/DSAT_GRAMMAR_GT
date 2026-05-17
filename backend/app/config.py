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

    # LLM
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

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
    default_annotation_model: str = "qwen3-vl:235b-instruct-cloud"
    default_ollama_model: str = "qwen3-vl:235b-instruct-cloud"
    rules_version: str = "rules_agent_dsat_grammar_ingestion_generation_v3"
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
    pipeline_timeout_s: int = 1800
    # Output token budget for Pass 1 extraction. A full 27-question module of
    # JSON exceeds 16K tokens for large modules; too low a cap truncates the
    # JSON mid-array and the parse fails.
    extraction_max_tokens: int = 32000
    # Background sweeper interval — marks jobs stuck in in-progress statuses
    # longer than pipeline_timeout_s as failed. 0 disables the sweeper.
    job_sweeper_interval_s: int = 300

    # OCR / Vision — Option B: Ollama VLM (fused)
    ocr_vision_provider: str = "ollama"
    ocr_vision_model: str = "qwen3.0-vl"
    ocr_strategy: str = "glm"  # glm | deepseek | ollama | anthropic | openai | auto
    ocr_fallback: bool = True
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
