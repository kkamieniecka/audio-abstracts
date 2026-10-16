import pytest

from audio_abstracts.client import (
    DEFAULT_VOICE,
    PHONEME_RULE_MODELS,
    DictionaryRef,
    ElevenLabsClient,
    ElevenLabsError,
    Prepared,
)
from audio_abstracts.lexicon import Rule

from .conftest import StubResponse, StubSession


def test_missing_key_is_rejected_unless_dry_running():
    with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
        ElevenLabsClient(api_key=None)
    assert ElevenLabsClient(dry_run=True).api_key == ""


def test_text_to_speech_request_shape():
    session = StubSession(StubResponse(content=b"ID3audio"))
    client = ElevenLabsClient(api_key="k", session=session)

    audio = client.text_to_speech("CpG islands", voice_id="VOICE", model_id="eleven_v3")

    assert audio == b"ID3audio"
    call = session.last
    assert call["method"] == "POST"
    assert call["url"].endswith("/v1/text-to-speech/VOICE")
    assert call["headers"]["xi-api-key"] == "k"
    assert call["params"] == {"output_format": "mp3_44100_128"}
    assert call["json"] == {"text": "CpG islands", "model_id": "eleven_v3"}
    assert "pronunciation_dictionary_locators" not in call["json"]


def test_locators_are_sent_as_id_and_version_pairs():
    session = StubSession(StubResponse(content=b""))
    client = ElevenLabsClient(api_key="k", session=session)
    client.text_to_speech("x", dictionaries=[DictionaryRef("dict1", "ver1")])

    assert session.last["json"]["pronunciation_dictionary_locators"] == [
        {"pronunciation_dictionary_id": "dict1", "version_id": "ver1"}
    ]


def test_more_than_three_dictionaries_is_refused_before_the_request():
    session = StubSession()
    client = ElevenLabsClient(api_key="k", session=session)
    refs = [DictionaryRef(f"d{i}", f"v{i}") for i in range(4)]

    with pytest.raises(ValueError, match="at most 3"):
        client.text_to_speech("x", dictionaries=refs)
    assert session.calls == [], "no request should leave the process"


def test_add_rules_returns_the_new_version_id():
    session = StubSession(StubResponse({"id": "dict1", "version_id": "ver2"}))
    client = ElevenLabsClient(api_key="k", session=session)

    ref = client.add_rules("dict1", [Rule("CpG", "alias", "see pee gee")])

    assert ref == DictionaryRef("dict1", "ver2")
    assert session.last["json"] == {
        "rules": [{"string_to_replace": "CpG", "type": "alias", "alias": "see pee gee"}]
    }


def test_create_dictionary_uploads_the_pls_file_as_multipart(tmp_path):
    pls = tmp_path / "x.pls"
    pls.write_text('<?xml version="1.0"?><lexicon version="1.0"/>')
    session = StubSession(StubResponse({"id": "d", "version_id": "v"}))
    client = ElevenLabsClient(api_key="k", session=session)

    ref = client.create_dictionary_from_file(pls, name="demo", description="d")

    assert ref == DictionaryRef("d", "v")
    assert session.last["url"].endswith("/v1/pronunciation-dictionaries/add-from-file")
    assert "file" in session.last["files"]
    assert session.last["data"] == {"name": "demo", "description": "d"}


def test_phoneme_rejection_is_explained():
    session = StubSession(
        StubResponse({"detail": "pronunciation dictionary not supported"}, status_code=422)
    )
    client = ElevenLabsClient(api_key="k", session=session)

    with pytest.raises(ElevenLabsError) as excinfo:
        client.text_to_speech("x", dictionaries=[DictionaryRef("d", "v")])

    assert excinfo.value.status_code == 422
    assert "Phoneme rules are only" in excinfo.value.hint
    for model in PHONEME_RULE_MODELS:
        assert model in excinfo.value.hint


def test_unauthorised_names_the_environment_variable():
    session = StubSession(StubResponse({"detail": "unauthorized"}, status_code=401))
    client = ElevenLabsClient(api_key="bad", session=session)
    with pytest.raises(ElevenLabsError, match="ELEVENLABS_API_KEY"):
        client.list_voices()


def test_dry_run_builds_a_curl_command_and_sends_nothing():
    session = StubSession()
    client = ElevenLabsClient(session=session, dry_run=True)

    prepared = client.text_to_speech("CpG islands", dictionaries=[DictionaryRef("d", "v")])

    assert isinstance(prepared, Prepared)
    assert session.calls == []
    curl = prepared.as_curl()
    assert f"/v1/text-to-speech/{DEFAULT_VOICE}?output_format=mp3_44100_128" in curl
    assert "$ELEVENLABS_API_KEY" in curl
    assert "pronunciation_dictionary_locators" in curl


def test_dry_run_never_leaks_a_real_key():
    client = ElevenLabsClient(api_key="secret-key", session=StubSession(), dry_run=True)
    prepared = client.text_to_speech("x")
    assert "secret-key" not in prepared.as_curl()
