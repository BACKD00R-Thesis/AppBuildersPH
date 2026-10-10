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


KID = Character(
    id="kid", name="Kid", role="asker", persona="", color="#F27BA5",
    voices={"kokoro": "af_bella", "chatterbox": "voices/kid.wav"},
)  # fmt: skip


def test_audio_key_depends_on_voice_style_and_mood():
    settings = get_settings()
    quick = tts.audio_key(TEXT, KID, settings)
    assert quick == tts.audio_key(TEXT, KID, settings, "quick", "gets")  # quick voices aren't acted
    excited = tts.audio_key(TEXT, KID, settings, "expressive", "gets")
    bored = tts.audio_key(TEXT, KID, settings, "expressive", "bored")
    assert len({quick, excited, bored}) == 3


def test_kid_voice_shift_gets_its_own_audio():
    settings = get_settings().model_copy(update={"tts_engine": "kokoro"})  # dummy blips aren't shifted
    shifted = Character(**{**KID.__dict__, "pitch_shift": 4})
    assert tts.audio_key(TEXT, KID, settings) != tts.audio_key(TEXT, shifted, settings)


def test_expressive_voice_comes_from_the_characters_folder():
    settings = get_settings()
    assert tts.voice_for(KID, settings, "expressive") == str(
        settings.assets_dir / "characters" / "voices/kid.wav"
    )
    with pytest.raises(tts.TTSError, match="No expressive voice"):
        tts.voice_for(DEX, settings, "expressive")


@needs_ffmpeg
def test_acted_lines_only_move_to_the_nearest_edge(tmp_path):
    path = tmp_path / "slow.wav"
    tts._dummy(TEXT, DEX, path, words_per_second=1.8)  # a deliberately slow, bored line
    tts.pace_clip(path, 8, get_settings(), tts.EXPRESSIVE_WPS, nearest_edge=True)
    assert tts.speech_rate(path, 8) == pytest.approx(tts.EXPRESSIVE_WPS[0], rel=0.03)
