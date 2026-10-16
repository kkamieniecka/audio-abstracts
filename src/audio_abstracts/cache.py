"""Remember uploaded dictionaries so we do not re-upload on every run.

A pronunciation dictionary is a durable server-side resource, but nothing
in the API stops you creating a fresh duplicate on each invocation. The
cache is keyed on the SHA-256 of the lexicon file, so editing the lexicon
transparently forces a new upload and leaving it alone reuses the old
one.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .client import DictionaryRef


def cache_path() -> Path:
    root = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(root) / "audio-abstracts" / "dictionaries.json"


def fingerprint(path: str | Path) -> str:
    """SHA-256 of a lexicon file, truncated for readability in the cache."""
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return digest[:16]


def _read() -> dict[str, dict[str, str]]:
    path = cache_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def lookup(key: str) -> DictionaryRef | None:
    entry = _read().get(key)
    if not entry:
        return None
    return DictionaryRef(entry["pronunciation_dictionary_id"], entry["version_id"])


def remember(key: str, ref: DictionaryRef) -> None:
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _read()
    data[key] = ref.as_locator()
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
