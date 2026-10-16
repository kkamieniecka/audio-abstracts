"""A small, inspectable ElevenLabs HTTP client.

This is deliberately `requests` rather than the official SDK. The demo
doubles as documentation of the HTTP surface, so the request it builds
should be visible, printable, and portable to any language -- see
`examples/with_sdk.py` for the same pipeline in a dozen lines of the
official Python SDK, which is what you would reach for in production.

Every method takes an injectable session, and `dry_run=True` returns the
prepared request instead of sending it, so the whole pipeline is testable
without a key or a network.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from .lexicon import Rule

BASE_URL = "https://api.elevenlabs.io"

# George, one of the documented default voices: a neutral British
# narration voice, which suits read-aloud scientific prose.
DEFAULT_VOICE = "JBFqnCBsd6RMkjVDRZzb"
DEFAULT_MODEL = "eleven_v3"

# Alias rules work on every text-to-speech model. Phoneme rules do not.
# This set reflects the documented position at the time of writing; model
# availability moves, so treat it as a hint and confirm with
# `audio-abstracts doctor`, which asks the API directly.
PHONEME_RULE_MODELS = frozenset({"eleven_v3", "eleven_v4", "eleven_v4_turbo", "eleven_flash_v2"})

# The API applies dictionaries in order and caps how many travel with one
# request; exceeding the cap is a 422 that is easy to misread.
MAX_DICTIONARIES_PER_REQUEST = 3


class ElevenLabsError(RuntimeError):
    """An API call failed. Carries the status code and the server's body."""

    def __init__(self, status_code: int, body: str, hint: str = "") -> None:
        self.status_code = status_code
        self.body = body
        self.hint = hint
        message = f"ElevenLabs API returned {status_code}: {body[:500]}"
        if hint:
            message += f"\n\nLikely cause: {hint}"
        super().__init__(message)


@dataclass(frozen=True)
class DictionaryRef:
    """Identifies one *version* of an uploaded pronunciation dictionary.

    Both halves matter. Adding rules creates a new version, and a request
    that quotes a stale `version_id` silently uses the old rules, which is
    a confusing way to lose an afternoon.
    """

    pronunciation_dictionary_id: str
    version_id: str

    def as_locator(self) -> dict[str, str]:
        return {
            "pronunciation_dictionary_id": self.pronunciation_dictionary_id,
            "version_id": self.version_id,
        }


@dataclass(frozen=True)
class Prepared:
    """A request that was built but not sent (dry-run mode)."""

    method: str
    url: str
    headers: dict[str, str]
    body: str

    def as_curl(self) -> str:
        parts = [f"curl -X {self.method}", shlex.quote(self.url)]
        for key, value in self.headers.items():
            parts.append(f"-H {shlex.quote(f'{key}: {value}')}")
        if self.body:
            parts.append(f"-d {shlex.quote(self.body)}")
        return " \\\n  ".join(parts)


def _hint_for(status_code: int, body: str) -> str:
    """Translate the statuses this demo actually provokes into English."""
    lowered = body.lower()
    if status_code == 401:
        return "the key in ELEVENLABS_API_KEY is missing, revoked, or mistyped"
    if status_code == 404 and "voice" in lowered:
        return "that voice_id is not in your library; run the `voices` subcommand"
    if status_code == 422 and "pronunciation" in lowered:
        return (
            "a pronunciation dictionary was rejected. Phoneme rules are only "
            f"honoured by {sorted(PHONEME_RULE_MODELS)}; with any other model, "
            "use alias rules instead"
        )
    if status_code == 422:
        return "the request body failed validation; check model_id and voice_settings"
    if status_code == 429:
        return "rate limit or concurrency cap reached; retry with backoff"
    return ""


class ElevenLabsClient:
    """Thin wrapper over the endpoints this demo needs."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        session: requests.Session | None = None,
        dry_run: bool = False,
    ) -> None:
        if not api_key and not dry_run:
            raise ValueError(
                "No API key. Set ELEVENLABS_API_KEY, or pass dry_run=True to "
                "build requests without sending them."
            )
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.dry_run = dry_run

    # -- plumbing ---------------------------------------------------------

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"xi-api-key": self.api_key}
        headers.update(extra or {})
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> requests.Response | Prepared:
        url = f"{self.base_url}{path}"
        if self.dry_run:
            return Prepared(
                method=method,
                url=url if not params else f"{url}?{_querystring(params)}",
                headers=self._headers({"Content-Type": "application/json"} if json_body else None)
                | {"xi-api-key": "$ELEVENLABS_API_KEY"},
                body=json.dumps(json_body, indent=2, ensure_ascii=False) if json_body else "",
            )
        response = self.session.request(
            method,
            url,
            headers=self._headers(),
            params=params,
            json=json_body,
            files=files,
            data=data,
            stream=stream,
            timeout=120,
        )
        if response.status_code >= 400:
            body = response.text
            raise ElevenLabsError(response.status_code, body, _hint_for(response.status_code, body))
        return response

    # -- discovery --------------------------------------------------------

    def list_voices(self) -> list[dict[str, Any]]:
        """GET /v1/voices -- the voices available to this key."""
        response = self._request("GET", "/v1/voices")
        return response.json().get("voices", [])  # type: ignore[union-attr]

    def list_models(self) -> list[dict[str, Any]]:
        """GET /v1/models -- model ids, languages and capability flags."""
        response = self._request("GET", "/v1/models")
        return response.json()  # type: ignore[union-attr]

    # -- pronunciation dictionaries ---------------------------------------

    def create_dictionary_from_file(
        self,
        path: str | Path,
        name: str,
        description: str = "",
        workspace_access: str | None = None,
    ) -> DictionaryRef:
        """POST /v1/pronunciation-dictionaries/add-from-file.

        Multipart, not JSON: the PLS file is uploaded as `file`. Returns
        the id/version pair needed to reference it from a speech request.
        """
        path = Path(path)
        if self.dry_run:
            return DictionaryRef("dry-run-dictionary-id", "dry-run-version-id")
        payload: dict[str, Any] = {"name": name}
        if description:
            payload["description"] = description
        if workspace_access:
            payload["workspace_access"] = workspace_access
        with path.open("rb") as handle:
            response = self._request(
                "POST",
                "/v1/pronunciation-dictionaries/add-from-file",
                files={"file": (path.name, handle, "application/xml")},
                data=payload,
            )
        body = response.json()  # type: ignore[union-attr]
        return DictionaryRef(body["id"], body["version_id"])

    def add_rules(self, dictionary_id: str, rules: Sequence[Rule]) -> DictionaryRef:
        """POST /v1/pronunciation-dictionaries/{id}/add-rules.

        Returns a ref carrying the NEW version_id; use it, not the one you
        got at creation time.
        """
        if self.dry_run:
            return DictionaryRef(dictionary_id, "dry-run-version-id")
        response = self._request(
            "POST",
            f"/v1/pronunciation-dictionaries/{dictionary_id}/add-rules",
            json_body={"rules": [rule.as_payload() for rule in rules]},
        )
        body = response.json()  # type: ignore[union-attr]
        return DictionaryRef(body.get("id", dictionary_id), body["version_id"])

    # -- speech -----------------------------------------------------------

    def text_to_speech(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE,
        model_id: str = DEFAULT_MODEL,
        output_format: str = "mp3_44100_128",
        dictionaries: Iterable[DictionaryRef] = (),
        voice_settings: dict[str, Any] | None = None,
    ) -> bytes | Prepared:
        """POST /v1/text-to-speech/{voice_id} -- returns audio bytes."""
        locators = [ref.as_locator() for ref in dictionaries]
        if len(locators) > MAX_DICTIONARIES_PER_REQUEST:
            raise ValueError(
                f"{len(locators)} dictionaries requested but the API accepts at "
                f"most {MAX_DICTIONARIES_PER_REQUEST} per call"
            )
        body: dict[str, Any] = {"text": text, "model_id": model_id}
        if locators:
            body["pronunciation_dictionary_locators"] = locators
        if voice_settings:
            body["voice_settings"] = voice_settings
        result = self._request(
            "POST",
            f"/v1/text-to-speech/{voice_id}",
            params={"output_format": output_format},
            json_body=body,
            stream=True,
        )
        if isinstance(result, Prepared):
            return result
        return result.content


def _querystring(params: dict[str, Any]) -> str:
    from urllib.parse import urlencode

    return urlencode({k: v for k, v in params.items() if v is not None})
