"""Settings read from the environment (and the repo-root .env). See .env.example."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SERVER_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", SERVER_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        # Treat KEY= (blank) in .env as "not set" so defaults apply.
        env_ignore_empty=True,
    )

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_pairing_token: str = ""
    api_cors_origins: str = ""

    data_dir: Path = REPO_ROOT / "data"
    models_dir: Path = REPO_ROOT / "models"
    assets_dir: Path = REPO_ROOT / "assets"
    database_url: str = ""

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_s: float = 180.0

    # kokoro | piper | dummy (silent placeholder audio, for development without models)
    tts_engine: str = "kokoro"
    kokoro_voice_a: str = ""
    kokoro_voice_b: str = ""
    piper_voice_a: str = ""
    piper_voice_b: str = ""

    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    ffmpeg_path: str = "ffmpeg"
    render_width: int = 1080
    render_height: int = 1920
    render_fps: int = 30

    # Product limits (docs/product.md, FR-1)
    max_pdf_pages: int = 50
    max_pdf_bytes: int = 20 * 1024 * 1024

    @property
    def db_url(self) -> str:
        return self.database_url or f"sqlite:///{(self.data_dir / 'brainrot.db').as_posix()}"

    @property
    def projects_dir(self) -> Path:
        return self.data_dir / "projects"


@lru_cache
def get_settings() -> Settings:
    return Settings()
