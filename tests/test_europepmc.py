import pytest

from audio_abstracts.europepmc import NotFound, build_query, fetch_record

from .conftest import StubResponse, StubSession


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("10.1101/553784", "DOI:10.1101/553784"),
        ("31216044", "EXT_ID:31216044"),
        ("PMC6612819", "PMCID:PMC6612819"),
        ("pmc6612819", "PMCID:PMC6612819"),
        ("cross-array harmonisation", "cross-array harmonisation"),
    ],
)
def test_build_query_routes_identifier_types(identifier, expected):
    assert build_query(identifier) == expected


def test_fetch_record_maps_core_fields(europepmc_payload):
    session = StubSession(StubResponse(europepmc_payload))
    record = fetch_record("10.1101/553784", session=session)

    assert record.doi == "10.1101/553784"
    assert record.source == "PPR"
    assert record.title.startswith("EWAS-Galaxy")
    assert record.first_author == "Murat"
    assert "<h4>" in record.abstract, "raw markup is preserved for the normaliser to handle"
    assert session.last["params"]["query"] == "DOI:10.1101/553784"


def test_fetch_record_raises_on_empty_result_list():
    session = StubSession(StubResponse({"resultList": {"result": []}}))
    with pytest.raises(NotFound, match="no record"):
        fetch_record("10.0000/nope", session=session)
