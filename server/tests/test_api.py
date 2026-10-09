"""End-to-end API flow with the dummy TTS and a stubbed LLM."""

import time

import pytest

from app.config import get_settings
from app.pipeline import script as script_module
from app.pipeline.script import Script, ScriptError, ScriptLine
from tests.conftest import needs_ffmpeg


@pytest.fixture
def fake_llm(monkeypatch):
    def fake(material, asker, explainer, settings, client=None):
        return Script(
            title="Plants Eat Light",
            lines=[
                ScriptLine(asker.id, "Wait, plants eat light?"),
                ScriptLine(explainer.id, "Basically. Sunlight is their lunch money."),
                ScriptLine(asker.id, "Where does the oxygen come from?"),
                ScriptLine(explainer.id, "From splitting water. Recap: light in, sugar and oxygen out."),
            ],
        )

    monkeypatch.setattr(script_module, "generate_script", fake)


def wait_for(client, url, done, timeout=60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(url).json()
        if done(body):
            return body
        time.sleep(0.1)
    raise AssertionError(f"Timed out waiting on {url}: {body}")


def upload(client, pdf, **form):
    return client.post("/projects", files={"file": ("photosynthesis.pdf", pdf, "application/pdf")}, data=form)


def scripted_project(client, pdf):
    project = upload(client, pdf).json()
    client.post(f"/projects/{project['id']}/script")
    return wait_for(client, f"/projects/{project['id']}", lambda p: p["status"] != "generating")


def test_health(client):
    body = client.get("/health").json()
    assert body["ok"] is True
    assert body["auth_required"] is False
    assert set(body["engines"]) == {"llm", "tts", "alignment", "ffmpeg"}


def test_pairing_token_required(client, monkeypatch):
    monkeypatch.setenv("API_PAIRING_TOKEN", "s3cret")
    get_settings.cache_clear()
    assert client.get("/projects").status_code == 401
    assert client.get("/projects", headers={"X-Pairing-Token": "s3cret"}).status_code == 200
    assert client.get("/projects?token=s3cret").status_code == 200
    assert client.get("/health").json()["auth_ok"] is False


def test_assets(client):
    characters = client.get("/assets/characters").json()
    assert {c["role"] for c in characters} == {"asker", "explainer"}
    backgrounds = client.get("/assets/backgrounds").json()
    assert "builtin-life" in {b["id"] for b in backgrounds}


def test_upload_rejects_bad_files(client):
    response = client.post("/projects", files={"file": ("x.pdf", b"nope", "application/pdf")})
    assert response.status_code == 422


def test_upload_and_generate_script(client, sample_pdf, fake_llm):
    created = upload(client, sample_pdf, pages="1")
    assert created.status_code == 201
    assert created.json()["status"] == "ready"
    assert created.json()["pages"] == "1"

    project = scripted_project(client, sample_pdf)
    assert project["status"] == "scripted"
    assert project["title"] == "Plants Eat Light"  # filename title replaced by the model's
    assert [line["character_id"] for line in project["lines"]] == ["dex", "nova", "dex", "nova"]
    assert client.get("/projects").json()[0]["id"] == project["id"]


def test_script_failure_is_reported(client, sample_pdf, monkeypatch):
    def broken(*args, **kwargs):
        raise ScriptError("Couldn't reach Ollama")

    monkeypatch.setattr(script_module, "generate_script", broken)
    project = scripted_project(client, sample_pdf)
    assert project["status"] == "failed"
    assert "Ollama" in project["error"]


def test_edit_script_keeps_ids_and_preview_audio(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    first, second = project["lines"][0], project["lines"][1]

    preview = client.post(f"/lines/{first['id']}/preview")
    assert preview.status_code == 200
    audio = client.get(preview.json()["audio_url"])
    assert audio.headers["content-type"] == "audio/wav"

    edited = client.put(
        f"/projects/{project['id']}/script",
        json={
            "lines": [
                {"id": second["id"], "character_id": "nova", "text": "Moved   to the top."},
                {"id": first["id"], "character_id": "dex", "text": first["text"]},
                {"character_id": "dex", "text": "A brand new line."},
            ]
        },
    ).json()
    assert [line["text"] for line in edited["lines"]] == [
        "Moved to the top.",
        first["text"],
        "A brand new line.",
    ]
    assert edited["lines"][1]["id"] == first["id"]
    # Unchanged text reuses the cached clip.
    assert client.post(f"/lines/{first['id']}/preview").json()["audio_url"] == preview.json()["audio_url"]


def test_save_script_rejects_unknown_character(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    response = client.put(
        f"/projects/{project['id']}/script",
        json={"lines": [{"character_id": "peter", "text": "Hey Lois"}]},
    )
    assert response.status_code == 422


@needs_ffmpeg
def test_render_produces_video(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    started = client.post(f"/projects/{project['id']}/renders", json={"background_id": "builtin-plain"})
    assert started.status_code == 202
    render = wait_for(
        client, f"/renders/{started.json()['id']}", lambda r: r["status"] in ("done", "failed"), timeout=180
    )
    assert render["status"] == "done", render["error"]
    assert render["progress"] == 1.0
    video = client.get(render["video_url"])
    assert video.status_code == 200
    assert video.headers["content-type"] == "video/mp4"
    assert len(video.content) > 10_000


def test_render_requires_known_background(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    response = client.post(f"/projects/{project['id']}/renders", json={"background_id": "subway-surfers"})
    assert response.status_code == 422


def test_delete_project(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    assert client.delete(f"/projects/{project['id']}").status_code == 204
    assert client.get(f"/projects/{project['id']}").status_code == 404
