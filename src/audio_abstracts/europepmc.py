"""Fetch abstracts from Europe PMC.

Europe PMC needs no API key and no registration, which keeps the demo's
first step free of credentials -- you can run `audio-abstracts script`
before you have signed up for anything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import requests

SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

_DOI = re.compile(r"^10\.\d{4,9}/\S+$")
_PMID = re.compile(r"^\d{5,9}$")
_PMCID = re.compile(r"^PMC\d+$", re.IGNORECASE)


class NotFound(LookupError):
    """No Europe PMC record matched the identifier."""


@dataclass(frozen=True)
class Record:
    """The handful of fields needed to narrate a paper."""

    id: str
    source: str
    title: str
    abstract: str
    authors: str = ""
    journal: str = ""
    year: str = ""
    doi: str = ""

    @property
    def first_author(self) -> str:
        """Surname of the first author, or "" if unknown."""
        if not self.authors:
            return ""
        return self.authors.split(",")[0].strip().split(" ")[0]


def build_query(identifier: str) -> str:
    """Map a bare identifier onto a Europe PMC field query.

    Anything that is not recognisably a DOI, PMID or PMCID is passed
    through as a free-text query, so titles work too.
    """
    ident = identifier.strip()
    if _DOI.match(ident):
        return f"DOI:{ident}"
    if _PMID.match(ident):
        return f"EXT_ID:{ident}"
    if _PMCID.match(ident):
        return f"PMCID:{ident.upper()}"
    return ident


def fetch_record(identifier: str, session: requests.Session | None = None) -> Record:
    """Return the Europe PMC record for `identifier`.

    Raises NotFound if the search returns no results, which is the common
    case for very recent preprints and for typo'd DOIs.
    """
    http = session or requests.Session()
    response = http.get(
        SEARCH_URL,
        params={
            "query": build_query(identifier),
            "resultType": "core",
            "format": "json",
            "pageSize": 1,
        },
        timeout=30,
    )
    response.raise_for_status()
    results = response.json().get("resultList", {}).get("result", [])
    if not results:
        raise NotFound(f"Europe PMC has no record for {identifier!r}")
    return _to_record(results[0])


def _to_record(payload: dict[str, Any]) -> Record:
    return Record(
        id=payload.get("id", ""),
        source=payload.get("source", ""),
        title=(payload.get("title") or "").strip(),
        abstract=payload.get("abstractText") or "",
        authors=payload.get("authorString") or "",
        journal=payload.get("journalTitle") or "",
        year=str(payload.get("pubYear") or ""),
        doi=payload.get("doi") or "",
    )
