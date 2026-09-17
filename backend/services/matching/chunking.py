"""Source-preserving document chunks for matching extraction."""

from __future__ import annotations

from dataclasses import dataclass

MAX_DOCUMENT_CHARS = 100_000
MAX_CHUNK_CHARS = 8_000
CHUNK_OVERLAP_CHARS = 400


@dataclass(frozen=True, slots=True)
class TextChunk:
    start: int
    end: int
    text: str


def _preferred_end(text: str, start: int, limit: int) -> int:
    if limit == len(text):
        return limit

    for delimiter in ("\n\n", "\n"):
        boundary = text.rfind(delimiter, start + CHUNK_OVERLAP_CHARS, limit + 1)
        if boundary != -1:
            return boundary + len(delimiter)
    return limit


def chunk_text(text: str) -> list[TextChunk]:
    """Split accepted source text without changing its coordinates or contents."""
    if len(text) > MAX_DOCUMENT_CHARS:
        raise ValueError(
            f"Document text exceeds maximum limit of {MAX_DOCUMENT_CHARS:,} characters."
        )
    if not text:
        return []

    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = _preferred_end(text, start, min(start + MAX_CHUNK_CHARS, len(text)))
        chunks.append(TextChunk(start=start, end=end, text=text[start:end]))
        if end == len(text):
            break
        start = end - CHUNK_OVERLAP_CHARS

    return chunks
