import os
import re
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Canonical project root directory (C:\chromaNexus)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_FILE = _PROJECT_ROOT / "chronanexus.db"
_DEFAULT_DATABASE_URL = f"sqlite:///{_DEFAULT_DB_FILE.as_posix()}"


class Settings(BaseSettings):
    PROJECT_NAME: str = "ChronaNexus Medical Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "chronanexus-super-secure-change-in-production-secret-key-32bytes")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    DATABASE_URL: str = _DEFAULT_DATABASE_URL
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # Vector Store Configuration
    VECTOR_STORE_BACKEND: str = os.getenv("VECTOR_STORE_BACKEND", "chroma")  # 'chroma', 'postgres', 'in_memory'
    CHROMA_PERSIST_DIRECTORY: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        str((_PROJECT_ROOT / "data" / "chroma_db").as_posix())
    )
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "chronanexus_clinical_chunks")

    # AI & RAG Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")  # 'ollama', 'gemini', 'mock'
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "all-minilm")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "ollama")  # 'ollama', 'local'
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "auto")  # 'auto', 'tesseract', 'mock'
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # 'development', 'staging', 'production'
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    STRICT_SECURITY: bool = os.getenv("STRICT_SECURITY", "false").lower() in ("true", "1")

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(_PROJECT_ROOT / ".env"),
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Union[str, None]) -> str:
        if not v:
            return _DEFAULT_DATABASE_URL
        if v.startswith("sqlite:///"):
            path_part = v[len("sqlite:///"):]
            if re.match(r"^[a-zA-Z]:[/\\].*", path_part) or path_part.startswith("/"):
                return v
            clean_rel = path_part.lstrip("./\\")
            abs_path = (_PROJECT_ROOT / clean_rel).resolve()
            return f"sqlite:///{abs_path.as_posix()}"
        return v

    def validate_runtime_configuration(self) -> dict:
        """
        Validates runtime configuration and returns actionable diagnostics.
        Enforces strict constraints for production mode while keeping dev flexible.
        """
        issues = []
        warnings = []

        # 1. Secret key security check
        if self.SECRET_KEY == "chronanexus-super-secure-change-in-production-secret-key-32bytes":
            if self.ENVIRONMENT == "production" or self.STRICT_SECURITY:
                issues.append("Production or strict security active, but default SECRET_KEY is in use.")
            else:
                warnings.append("Using default development SECRET_KEY. Change in production environment.")

        # 2. Upload directory check
        try:
            os.makedirs(self.UPLOAD_DIR, exist_ok=True)
            probe = os.path.join(self.UPLOAD_DIR, ".write_probe")
            with open(probe, "w") as f:
                f.write("ok")
            os.remove(probe)
        except Exception as e:
            issues.append(f"Upload directory '{self.UPLOAD_DIR}' is not writable: {e}")

        # 3. Chroma directory check
        if self.VECTOR_STORE_BACKEND == "chroma":
            try:
                os.makedirs(self.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            except Exception as e:
                issues.append(f"Chroma persist directory '{self.CHROMA_PERSIST_DIRECTORY}' cannot be created: {e}")

        # 4. Database URL validity check
        if not self.DATABASE_URL:
            issues.append("DATABASE_URL must be specified.")

        return {
            "valid": len(issues) == 0,
            "environment": self.ENVIRONMENT,
            "issues": issues,
            "warnings": warnings,
            "llm_provider": self.LLM_PROVIDER,
            "vector_store": self.VECTOR_STORE_BACKEND
        }


settings = Settings()


def setup_logging():
    """Configures structured, sanitized operational logging for ChronaNexus."""
    import logging
    numeric_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

