import pytest

from app.assets import Character
from app.config import get_settings
from app.pipeline import tts
from tests.conftest import needs_ffmpeg

DEX = Character(id="dex", name="Dex", role="asker", persona="curious", color="#3BC8FF")
TEXT = "Wait, plants literally eat sunlight every single day?"  # 8 words


def test_dummy_speaks_at_a_readable_pace(tmp_path):
    path = tmp_path / "line.wav"
    tts.synthesize(TEXT, DEX, path, get_settings())
    assert tts.MIN_WPS <= tts.speech_rate(path, 8) <= tts.MAX_WPS


@needs_ffmpeg
@pytest.mark.parametrize("wps", [4.5, 1.8])
def test_pace_clip_moves_rate_into_range(tmp_path, wps):
    path = tmp_path / "line.wav"
    tts._dummy(TEXT, DEX, path, words_per_second=wps)
    tts.pace_clip(path, 8, get_settings())
    assert tts.speech_rate(path, 8) == pytest.approx(tts.TARGET_WPS, rel=0.03)


def test_pace_clip_leaves_short_lines_alone(tmp_path):
    path = tmp_path / "line.wav"
    tts._dummy("Wait, what?", DEX, path, words_per_second=6)
    before = tts.wav_duration(path)
    tts.pace_clip(path, 2, get_settings())
    assert tts.wav_duration(path) == before


def test_pace_clip_keeps_clip_if_ffmpeg_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("FFMPEG_PATH", "definitely-not-ffmpeg")
    get_settings.cache_clear()
    path = tmp_path / "line.wav"
    tts._dummy(TEXT, DEX, path, words_per_second=5)
    tts.pace_clip(path, 8, get_settings())
    assert tts.speech_rate(path, 8) == pytest.approx(5, rel=0.01)
