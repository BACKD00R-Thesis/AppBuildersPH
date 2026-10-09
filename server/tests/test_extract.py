import pytest

from app.pipeline.extract import ExtractError, clean_text, extract_pdf, parse_pages
from tests.conftest import make_pdf


def test_parse_pages_defaults_to_all():
    assert parse_pages(None, 3) == [0, 1, 2]
    assert parse_pages("  ", 3) == [0, 1, 2]


def test_parse_pages_ranges_and_singles():
    assert parse_pages("1-2, 4", 5) == [0, 1, 3]
    assert parse_pages("3-99", 4) == [2, 3]  # clipped to the document


@pytest.mark.parametrize("spec", ["abc", "3-1", "0", "10-12"])
def test_parse_pages_rejects_bad_input(spec):
    with pytest.raises(ExtractError):
        parse_pages(spec, 5)


def test_clean_text_joins_hyphenation_and_drops_page_numbers():
    raw = "Photo-\nsynthesis is neat.\n12\n•\nPage 3\nThe end."
    assert clean_text(raw) == "Photosynthesis is neat. The end."


def test_extract_pdf(sample_pdf):
    result = extract_pdf(sample_pdf, None, max_pages=50)
    assert result.page_count == 2
    assert "Calvin cycle" in result.text
    assert "thylakoids" in result.text


def test_extract_pdf_page_selection(sample_pdf):
    result = extract_pdf(sample_pdf, "2", max_pages=50)
    assert "thylakoids" in result.text
    assert "Calvin" not in result.text


def test_extract_pdf_page_limit(sample_pdf):
    with pytest.raises(ExtractError, match="limit"):
        extract_pdf(sample_pdf, None, max_pages=1)


def test_extract_rejects_non_pdf():
    with pytest.raises(ExtractError, match="readable PDF"):
        extract_pdf(b"not a pdf", None, max_pages=50)


def test_extract_rejects_textless_pdf():
    with pytest.raises(ExtractError, match="text"):
        extract_pdf(make_pdf([""]), None, max_pages=50)
