"""Read W3C PLS lexicons and turn them into ElevenLabs dictionary rules.

PLS (Pronunciation Lexicon Specification) is the format the
`add-from-file` endpoint accepts, and it is worth using as your source of
truth even though you could POST rules as JSON: it is a W3C standard, it
is diffable in version control, and the same file works with other speech
engines. This module is the small adapter between the two
representations.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Literal

PLS_NS = "http://www.w3.org/2005/01/pronunciation-lexicon"
_LEXEME = f"{{{PLS_NS}}}lexeme"
_GRAPHEME = f"{{{PLS_NS}}}grapheme"
_ALIAS = f"{{{PLS_NS}}}alias"
_PHONEME = f"{{{PLS_NS}}}phoneme"

ALIAS_LEXICON = "life-science.pls"
PHONEME_LEXICON = "life-science-phonemes.pls"


class InvalidLexicon(ValueError):
    """The file is not a usable PLS lexicon."""


@dataclass(frozen=True)
class Rule:
    """One pronunciation rule, in the shape the rules endpoint expects."""

    string_to_replace: str
    type: Literal["alias", "phoneme"]
    value: str
    alphabet: str = "ipa"

    def as_payload(self) -> dict[str, Any]:
        """Serialise for POST /v1/pronunciation-dictionaries/{id}/add-rules."""
        if self.type == "alias":
            return {
                "string_to_replace": self.string_to_replace,
                "type": "alias",
                "alias": self.value,
            }
        return {
            "string_to_replace": self.string_to_replace,
            "type": "phoneme",
            "phoneme": self.value,
            "alphabet": self.alphabet,
        }


def lexicon_path(name: str = ALIAS_LEXICON) -> Path:
    """Absolute path to a lexicon shipped inside the package."""
    return Path(str(resources.files("audio_abstracts.data").joinpath(name)))


def load_pls(path: str | Path) -> list[Rule]:
    """Parse a PLS file into rules.

    Raises InvalidLexicon rather than a bare ParseError so that a typo in
    a hand-edited lexicon produces a message naming the file.
    """
    path = Path(path)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise InvalidLexicon(f"{path} is not well-formed XML: {exc}") from exc
    if not root.tag.endswith("lexicon"):
        raise InvalidLexicon(f"{path} has root <{root.tag}>, expected <lexicon>")

    default_alphabet = root.get("alphabet", "ipa")
    rules: list[Rule] = []
    for lexeme in root.findall(_LEXEME):
        grapheme = lexeme.findtext(_GRAPHEME, default="").strip()
        if not grapheme:
            continue
        alias = lexeme.findtext(_ALIAS)
        phoneme = lexeme.findtext(_PHONEME)
        if alias and alias.strip():
            rules.append(Rule(grapheme, "alias", alias.strip()))
        elif phoneme and phoneme.strip():
            rules.append(Rule(grapheme, "phoneme", phoneme.strip(), alphabet=default_alphabet))
    if not rules:
        raise InvalidLexicon(f"{path} contains no usable lexemes")
    return rules


def rules_from_pls(name: str = ALIAS_LEXICON) -> list[Rule]:
    """Rules from a bundled lexicon, by filename."""
    return load_pls(lexicon_path(name))


def coverage(text: str, rules: Iterable[Rule]) -> list[Rule]:
    """Subset of `rules` whose term actually occurs in `text`.

    The API applies the whole dictionary regardless, so this is purely a
    debugging aid: it answers "did my dictionary do anything?", which is
    the first question anyone asks when the audio still sounds wrong.
    Matching is whole-token so that "CI" does not match "Science".
    """
    hits: list[Rule] = []
    for rule in rules:
        pattern = re.compile(
            r"(?<![A-Za-z0-9])" + re.escape(rule.string_to_replace) + r"(?![A-Za-z0-9])"
        )
        if pattern.search(text):
            hits.append(rule)
    return hits


def write_pls(rules: Iterable[Rule], path: str | Path, language: str = "en-GB") -> Path:
    """Write rules back out as PLS, for round-tripping an edited lexicon."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<lexicon version="1.0" xmlns="{PLS_NS}" alphabet="ipa" xml:lang="{language}">',
    ]
    for rule in rules:
        tag = "alias" if rule.type == "alias" else "phoneme"
        lines.append(
            f"  <lexeme><grapheme>{_escape(rule.string_to_replace)}</grapheme>"
            f"<{tag}>{_escape(rule.value)}</{tag}></lexeme>"
        )
    lines.append("</lexicon>")
    path = Path(path)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
