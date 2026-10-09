import shutil
from collections.abc import Iterator

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_engine

SAMPLE_TEXT = (
    "Photosynthesis is the process plants use to turn light energy into chemical energy. "
    "Chlorophyll in the chloroplasts absorbs sunlight. Water is split, releasing oxygen. "
    "Carbon dioxide is fixed into glucose during the Calvin cycle."
)

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg not installed")


def make_pdf(pages: list[str]) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def sample_pdf() -> bytes:
    return make_pdf([SAMPLE_TEXT, "Page two: the light-dependent reactions happen in the thylakoids. 2"])


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch) -> Iterator[None]:
    """Each test gets its own data dir and database, the dummy TTS, and no pairing token."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MODELS_DIR", str(tmp_path / "models"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("TTS_ENGINE", "dummy")
    monkeypatch.setenv("API_PAIRING_TOKEN", "")
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    get_engine().dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
