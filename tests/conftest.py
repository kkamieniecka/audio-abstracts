"""Shared stubs. No test in this suite touches the network or needs a key."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from audio_abstracts.europepmc import _to_record

FIXTURES = Path(__file__).parent / "fixtures"


class StubResponse:
    def __init__(self, payload: Any = None, status_code: int = 200, content: bytes = b"") -> None:
        self._payload = payload
        self.status_code = status_code
        self.content = content
        self.text = (
            json.dumps(payload) if payload is not None else content.decode("utf-8", "replace")
        )

    def json(self) -> Any:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"unexpected status {self.status_code}")


class StubSession:
    """Records calls and replays canned responses in order."""

    def __init__(self, *responses: StubResponse) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> StubResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0) if self.responses else StubResponse({})

    def get(self, url: str, **kwargs: Any) -> StubResponse:
        return self.request("GET", url, **kwargs)

    @property
    def last(self) -> dict[str, Any]:
        return self.calls[-1]


@pytest.fixture
def europepmc_payload() -> dict[str, Any]:
    return json.loads((FIXTURES / "ewas_galaxy.json").read_text())


@pytest.fixture
def record(europepmc_payload: dict[str, Any]):
    return _to_record(europepmc_payload["resultList"]["result"][0])
