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

    # LLM defaults
    default_annotation_provider: str = "anthropic"
    default_annotation_model: str = "claude-sonnet-4-6"
    rules_version: str = "rules_agent_dsat_grammar_ingestion_generation_v3"

    # Retry
    llm_retry_max_attempts: int = 3
    llm_retry_base_delay_s: float = 1.0
    llm_retry_max_delay_s: float = 30.0

    # OCR / Vision
    ocr_vision_provider: str = "ollama"
    ocr_vision_model: str = "qwen2.5-vl:7b"
    ocr_strategy: str = "auto"  # auto | vision | paddle | tesseract | easyocr
    ocr_fallback: bool = True
    vision_max_images: int = 10

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


def get_settings() -> Settings:
    return Settings()