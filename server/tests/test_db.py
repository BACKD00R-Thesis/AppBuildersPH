import sqlite3

from sqlmodel import Session

from app.config import get_settings
from app.db import get_engine, init_db
from app.models import CaptionStyle, Project


def test_init_db_upgrades_an_older_database(tmp_path, monkeypatch):
    """A database from before the new columns keeps working: they're added with their defaults."""
    db_path = tmp_path / "old.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE project (id VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, "
            "status VARCHAR(10) NOT NULL, error VARCHAR, pdf_path VARCHAR NOT NULL, "
            "page_count INTEGER NOT NULL, pages VARCHAR, extracted_text VARCHAR NOT NULL, "
            "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
        )
        conn.execute(
            "INSERT INTO project VALUES ('p1', 'Old', 'SCRIPTED', NULL, 'x.pdf', 3, NULL, 'text', "
            "'2026-10-01 00:00:00', '2026-10-01 00:00:00')"
        )

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    get_settings.cache_clear()
    get_engine.cache_clear()
    init_db()
    with Session(get_engine()) as session:
        project = session.get(Project, "p1")
        assert project.caption_style == CaptionStyle.BOLD_POP
        assert project.taglish is True
        assert project.length_s == 60
        assert project.source_kind == "pdf"
        assert not project.key_ideas
