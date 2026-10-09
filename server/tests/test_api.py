"""End-to-end API flow with the dummy TTS and a stubbed LLM."""

import time

import pytest

from app.config import get_settings
from app.pipeline import script as script_module
from app.pipeline.script import Script, ScriptError, ScriptLine
from tests.conftest import needs_ffmpeg

NOTES = (
    "Photosynthesis turns light into sugar. Chlorophyll absorbs sunlight. Water is split, releasing oxygen."
)


@pytest.fixture
def fake_llm(monkeypatch):
    seen = {}

    def fake(material, asker, explainer, settings, options=None, client=None, on_step=None):
        seen["options"] = options
        for step in ("ideas", "jokes", "check"):
            on_step(step)
        return Script(
            title="Plants Eat Light",
            subject="Biology",
            key_ideas=["Light becomes sugar", "Water is split"],
            lines=[
                ScriptLine(asker.id, "Wait, plants eat light?"),
                ScriptLine(explainer.id, "Basically. Sunlight is their lunch money."),
                ScriptLine(asker.id, "Where does the oxygen come from?"),
                ScriptLine(explainer.id, "From splitting water. Recap: light in, sugar and oxygen out."),
            ],
        )

    monkeypatch.setattr(script_module, "generate_script", fake)
    return seen


def wait_for(client, url, done, timeout=60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(url).json()
        if done(body):
            return body
        time.sleep(0.1)
    raise AssertionError(f"Timed out waiting on {url}: {body}")


def upload(client, pdf, **form):
    return client.post(
        "/api/projects", files={"file": ("Week6_Photosynthesis.pdf", pdf, "application/pdf")}, data=form
    )


def scripted_project(client, pdf, **form):
    project = upload(client, pdf, **form).json()
    client.post(f"/api/projects/{project['id']}/script")
    return wait_for(client, f"/api/projects/{project['id']}", lambda p: p["status"] != "generating")


def test_health(client):
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["auth_required"] is False
    assert body["user_name"] == ""
    assert set(body["engines"]) == {"llm", "tts", "alignment", "ffmpeg"}


def test_pairing_token_required(client, monkeypatch):
    monkeypatch.setenv("API_PAIRING_TOKEN", "s3cret")
    get_settings.cache_clear()
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects", headers={"X-Pairing-Token": "s3cret"}).status_code == 200
    assert client.get("/api/projects?token=s3cret").status_code == 200
    assert client.get("/api/health").json()["auth_ok"] is False


def test_assets(client):
    characters = client.get("/api/assets/characters").json()
    assert [(c["id"], c["role"]) for c in characters] == [("tito-boy", "asker"), ("bunso", "explainer")]
    assert characters[0]["vibe"] == "Loud and slow"
    backgrounds = client.get("/api/assets/backgrounds").json()
    assert [b["id"] for b in backgrounds] == ["parkour", "kart", "blocks", "soap"]
    assert backgrounds[0]["from"].startswith("#") and backgrounds[0]["has_clip"] is False


def test_voice_sample(client):
    response = client.get("/api/assets/characters/bunso/sample")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert client.get("/api/assets/characters/peter/sample").status_code == 404


def test_upload_rejects_bad_input(client):
    assert (
        client.post("/api/projects", files={"file": ("x.pdf", b"nope", "application/pdf")}).status_code == 422
    )
    assert client.post("/api/projects", data={"notes": "too short"}).status_code == 422
    assert client.post("/api/projects", data={}).status_code == 422
    assert client.post("/api/projects", data={"notes": NOTES, "length_s": "45"}).status_code == 422


def test_create_from_notes_and_text_file(client):
    from_notes = client.post(
        "/api/projects", data={"notes": NOTES, "length_s": "30", "taglish": "false"}
    ).json()
    assert from_notes["source_kind"] == "notes"
    assert from_notes["title"] == "Pasted notes"
    assert (from_notes["length_s"], from_notes["taglish"]) == (30, False)
    from_file = client.post(
        "/api/projects", files={"file": ("ch1.md", f"# Chapter 1\n\n- {NOTES}".encode(), "text/markdown")}
    )
    assert from_file.json()["source_kind"] == "text"
    assert from_file.json()["text_preview"].startswith("Chapter 1")


def test_upload_and_generate_script(client, sample_pdf, fake_llm):
    created = upload(client, sample_pdf, pages="1", length_s="90")
    assert created.status_code == 201
    assert created.json()["status"] == "ready"
    assert created.json()["title"] == "Week6 Photosynthesis"
    assert created.json()["background_id"] == "parkour"

    project = scripted_project(client, sample_pdf, length_s="90", taglish="true")
    assert fake_llm["options"].length_s == 90 and fake_llm["options"].taglish is True
    assert project["status"] == "scripted"
    assert project["script_step"] is None
    assert project["title"] == "Plants Eat Light"  # file-name title replaced by the model's
    assert project["subject"] == "Biology"
    assert project["key_ideas"] == ["Light becomes sugar", "Water is split"]
    assert [line["character_id"] for line in project["lines"]] == ["tito-boy", "bunso", "tito-boy", "bunso"]
    assert project["lines"][0]["voiced"] is False and project["lines"][0]["seconds"] > 0

    summary = client.get("/api/projects").json()[0]
    assert summary["id"] == project["id"]
    assert summary["line_count"] == 4 and summary["subject"] == "Biology"


def test_renamed_title_is_kept(client, sample_pdf, fake_llm):
    project = upload(client, sample_pdf).json()
    client.patch(f"/api/projects/{project['id']}", json={"title": "My notes"})
    client.post(f"/api/projects/{project['id']}/script")
    done = wait_for(client, f"/api/projects/{project['id']}", lambda p: p["status"] != "generating")
    assert done["title"] == "My notes"


def test_script_failure_is_reported(client, sample_pdf, monkeypatch):
    def broken(*args, **kwargs):
        raise ScriptError("Couldn't reach Ollama")

    monkeypatch.setattr(script_module, "generate_script", broken)
    project = scripted_project(client, sample_pdf)
    assert project["status"] == "failed"
    assert "Ollama" in project["error"]


def test_patch_style(client, sample_pdf):
    project = upload(client, sample_pdf).json()
    url = f"/api/projects/{project['id']}"
    updated = client.patch(
        url, json={"background_id": "kart", "caption_style": "outline", "taglish": False}
    ).json()
    assert (updated["background_id"], updated["caption_style"], updated["taglish"]) == (
        "kart",
        "outline",
        False,
    )
    assert client.patch(url, json={"background_id": "subway-surfers"}).status_code == 422
    assert client.patch(url, json={"caption_style": "comic-sans"}).status_code == 422
    assert client.patch(url, json={"length_s": 45}).status_code == 422


def test_edit_script_keeps_ids_and_preview_audio(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    first, second = project["lines"][0], project["lines"][1]

    preview = client.post(f"/api/lines/{first['id']}/preview")
    assert preview.status_code == 200
    assert preview.json()["audio_url"].startswith("/api/lines/")
    audio = client.get(preview.json()["audio_url"])
    assert audio.headers["content-type"] == "audio/wav"
    voiced = client.get(f"/api/projects/{project['id']}").json()["lines"][0]
    assert voiced["voiced"] is True

    edited = client.put(
        f"/api/projects/{project['id']}/script",
        json={
            "lines": [
                {"id": second["id"], "character_id": "bunso", "text": "Moved   to the top."},
                {"id": first["id"], "character_id": "tito-boy", "text": first["text"]},
                {"character_id": "tito-boy", "text": "A brand new line."},
            ]
        },
    ).json()
    assert [line["text"] for line in edited["lines"]] == [
        "Moved to the top.",
        first["text"],
        "A brand new line.",
    ]
    assert edited["lines"][1]["id"] == first["id"]
    assert edited["lines"][1]["voiced"] is True  # unchanged text keeps its audio
    # Unchanged text reuses the cached clip.
    assert client.post(f"/api/lines/{first['id']}/preview").json()["audio_url"] == preview.json()["audio_url"]


def test_save_script_rejects_unknown_character(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    response = client.put(
        f"/api/projects/{project['id']}/script",
        json={"lines": [{"character_id": "peter", "text": "Hey Lois"}]},
    )
    assert response.status_code == 422


@needs_ffmpeg
@pytest.mark.parametrize("caption_style", ["bold-pop", "clean", "outline"])
def test_render_produces_video(client, sample_pdf, fake_llm, caption_style):
    project = scripted_project(client, sample_pdf)
    started = client.post(
        f"/api/projects/{project['id']}/renders",
        json={"background_id": "soap", "caption_style": caption_style},
    )
    assert started.status_code == 202
    render = wait_for(
        client,
        f"/api/renders/{started.json()['id']}",
        lambda r: r["status"] in ("done", "failed"),
        timeout=180,
    )
    assert render["status"] == "done", render["error"]
    assert render["progress"] == 1.0
    assert render["caption_style"] == caption_style
    video = client.get(render["video_url"])
    assert video.status_code == 200
    assert video.headers["content-type"] == "video/mp4"
    assert video.headers["content-disposition"].startswith("inline")
    assert len(video.content) > 10_000
    download = client.get(render["video_url"] + "?download=1")
    assert download.headers["content-disposition"].startswith("attachment")

    saved = client.get(f"/api/projects/{project['id']}").json()
    assert saved["video"]["id"] == render["id"]
    assert (saved["background_id"], saved["caption_style"]) == ("soap", caption_style)


def test_render_requires_known_background(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    response = client.post(f"/api/projects/{project['id']}/renders", json={"background_id": "subway-surfers"})
    assert response.status_code == 422


def test_delete_project(client, sample_pdf, fake_llm):
    project = scripted_project(client, sample_pdf)
    assert client.delete(f"/api/projects/{project['id']}").status_code == 204
    assert client.get(f"/api/projects/{project['id']}").status_code == 404


def test_serves_web_app_with_spa_fallback(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import create_app

    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<div id=root></div>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setenv("WEB_DIST_DIR", str(dist))
    get_settings.cache_clear()
    with TestClient(create_app()) as web:
        assert web.get("/").text == "<div id=root></div>"
        assert web.get("/videos/abc/script").text == "<div id=root></div>"  # client-side route
        assert web.get("/assets/app.js").headers["cache-control"].startswith("public")
        assert web.get("/api/health").json()["ok"] is True
        assert web.get("/api/nope").status_code == 404
        assert web.get("/../secret.txt").text == "<div id=root></div>"
