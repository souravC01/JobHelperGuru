import pytest


def test_chunks_cover_late_text():
    from backend.services.matching.chunking import chunk_text
    text = ("A paragraph about work.\n\n" * 600) + "LATE PROJECT"
    chunks = chunk_text(text)
    assert len(chunks) > 1 and chunks[0].start == 0 and chunks[-1].end == len(text)
    assert all(c.text == text[c.start:c.end] and len(c.text) <= 8000 for c in chunks)
    assert all(a.end >= b.start and b.start > a.start for a, b in zip(chunks, chunks[1:]))
    assert "LATE PROJECT" in chunks[-1].text
    assert chunk_text("") == []
    with pytest.raises(ValueError):
        chunk_text("x" * 100001)
