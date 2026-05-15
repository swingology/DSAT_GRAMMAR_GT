from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://dsat:dsat_dev@localhost:5434/dsat_dev"

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
    object_storage_layout_config: str = "config/storage_layout.yaml"
    object_storage_backend: str = "local_fs"
    object_storage_local_root: str = "../local_object_store"

    # LLM defaults
    default_annotation_provider: str = "ollama"
    default_annotation_model: str = "deepseek-v4-pro:cloud"
    default_ollama_model: str = "deepseek-v4-pro:cloud"
    rules_version: str = "rules_agent_dsat_grammar_ingestion_generation_v3"
    official_auto_activate_for_testing: bool = False

    # Retry
    llm_retry_max_attempts: int = 3
    llm_retry_base_delay_s: float = 1.0
    llm_retry_max_delay_s: float = 30.0

    # OCR / Vision — Option B: Ollama VLM (fused)
    ocr_vision_provider: str = "ollama"
    ocr_vision_model: str = "qwen2.5-vl:7b"
    ocr_strategy: str = "glm"  # glm | deepseek | ollama | anthropic | openai | auto
    ocr_fallback: bool = True
    vision_max_images: int = 10

    # OCR — Option A: DeepSeek OCR-2 (optional local server via vLLM Docker or LMDeploy)
    deepseek_ocr_base_url: str = ""
    deepseek_ocr_model: str = "deepseek-ai/DeepSeek-OCR-2"

    # OCR — Option G: GLM-OCR via Ollama (two-step: OCR then extraction LLM)
    glm_ocr_model: str = "glm-ocr:latest"

    # Logging
    log_level: str = "INFO"
    log_json: bool = True

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
