"""Turn a journal abstract into something a voice model can read aloud.

Abstracts are written to be *scanned*, not spoken. They carry HTML
section headings, bracketed citations, inline statistics and symbols that
a reader's eye jumps over but a voice model has to vocalise. This module
is the unglamorous half of the pipeline, and skipping it is the most
common reason a first text-to-speech attempt on scientific text sounds
wrong.

Lexical fixes ("CpG" -> "see pee gee") deliberately do NOT live here --
they belong in the pronunciation dictionary, so that they apply to any
text you send and can be reused outside this tool.
"""

from __future__ import annotations

import html
import re

from .europepmc import Record

# Structured abstracts arrive as "<h4>Background</h4> ..."; keep the
# heading as a spoken cue but make it a sentence so the model pauses.
_HEADING = re.compile(r"<h\d[^>]*>\s*(.*?)\s*</h\d>", re.IGNORECASE | re.DOTALL)
_PARAGRAPH_END = re.compile(r"</p\s*>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
# Bracketed citation groups: [1], [2,3], [4-6], [1, 2, 3]
_CITATION = re.compile(r"\s*\[\s*\d+(?:\s*[-,\u2013]\s*\d+)*\s*\]")
# URLs read aloud are unbearable, and they also trip the "/" rule below.
# Drop them, along with the parentheses that usually surround them.
_URL = re.compile(r"\s*\(?\s*(?:https?://|www\.)[^\s)]+\s*\)?")
_WHITESPACE = re.compile(r"[ \t\u00a0]+")
_BLANKS = re.compile(r"\n{3,}")

# Symbols and abbreviations a model either skips or mangles. Order
# matters: longer patterns first.
_SUBSTITUTIONS: tuple[tuple[str, str], ...] = (
    (r"\be\.\s?g\.", "for example"),
    (r"\bi\.\s?e\.", "that is"),
    (r"\bet\s+al\.", "and colleagues"),
    (r"\bvs\.?\b", "versus"),
    (r"\bFig(?:s)?\.", "Figure"),
    (r"\bca\.\s", "approximately "),
    (r"\u00b1", " plus or minus "),
    (r"\u2265", " greater than or equal to "),
    (r"\u2264", " less than or equal to "),
    (r"\u2260", " not equal to "),
    (r"\u2248", " approximately "),
    (r"(?<=\d)\s*[\u00d7x]\s*(?=\d)", " times "),
    (r"(?<=\d)\s*-\s*(?=\d)", " to "),
    (r"(?<=\d)\s*\u2013\s*(?=\d)", " to "),
    (r"~(?=\d)", "approximately "),
    (r"(?<=\d)\s*%", " percent"),
    (r"\u00b0\s?C\b", " degrees Celsius"),
    (r"[\u00b5\u03bc](?=[MmgLl]\b)", "micro"),
    (r"\s*&\s*", " and "),
    (r"(?<=[a-zA-Z])\s*/\s*(?=[a-zA-Z])", " or "),
    (r"<\s*(?=[\d.])", "less than "),
    (r">\s*(?=[\d.])", "greater than "),
)
_COMPILED = tuple((re.compile(pattern), repl) for pattern, repl in _SUBSTITUTIONS)


def normalise(text: str) -> str:
    """Strip markup and vocalise symbols, leaving clean spoken prose."""
    text = _HEADING.sub(r"\n\n\1. ", text)
    text = _PARAGRAPH_END.sub("\n\n", text)
    text = _TAG.sub(" ", text)
    text = html.unescape(text)
    text = _CITATION.sub("", text)
    text = _URL.sub("", text)
    for pattern, replacement in _COMPILED:
        text = pattern.sub(replacement, text)
    text = _WHITESPACE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    return _BLANKS.sub("\n\n", text).strip()


def build_script(record: Record, include_citation: bool = True) -> str:
    """Assemble the full narration script for a record.

    A spoken citation up front orients the listener the way a title slide
    would; `include_citation=False` gives you the abstract alone, which is
    what you want when stitching several papers into one digest.
    """
    blocks: list[str] = []
    if include_citation:
        blocks.append(normalise(record.title.rstrip(".")) + ".")
        credit = _spoken_credit(record)
        if credit:
            blocks.append(credit)
    body = normalise(record.abstract)
    if not body:
        raise ValueError(
            f"{record.id or 'record'} has no abstract text -- Europe PMC holds "
            "metadata only for some records"
        )
    blocks.append(body)
    return "\n\n".join(blocks)


def _spoken_credit(record: Record) -> str:
    """One sentence of provenance: who, where, when."""
    parts: list[str] = []
    if record.first_author:
        parts.append(f"{record.first_author} and colleagues")
    if record.journal:
        parts.append(f"writing in {record.journal}")
    elif record.source == "PPR":
        parts.append("in a preprint")
    if record.year:
        parts.append(f"in {record.year}")
    return " ".join(parts) + "." if parts else ""


def chunk(script: str, limit: int = 4800) -> list[str]:
    """Split a script into request-sized pieces at paragraph boundaries.

    The text-to-speech endpoint takes a few thousand characters per
    request; abstracts fit comfortably, but a multi-paper digest will
    not. Splitting on blank lines keeps each request a whole thought, so
    the prosody does not break mid-sentence.
    """
    if len(script) <= limit:
        return [script]
    chunks: list[str] = []
    current = ""
    for paragraph in script.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > limit and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
