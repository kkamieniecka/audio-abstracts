import pytest

from audio_abstracts.lexicon import (
    ALIAS_LEXICON,
    PHONEME_LEXICON,
    InvalidLexicon,
    Rule,
    coverage,
    lexicon_path,
    load_pls,
    rules_from_pls,
    write_pls,
)


def test_bundled_alias_lexicon_is_all_alias_rules():
    rules = rules_from_pls(ALIAS_LEXICON)
    assert len(rules) > 50
    assert {rule.type for rule in rules} == {"alias"}
    assert any(rule.string_to_replace == "CpG" for rule in rules)


def test_bundled_phoneme_lexicon_is_all_ipa_phoneme_rules():
    rules = rules_from_pls(PHONEME_LEXICON)
    assert rules
    assert {rule.type for rule in rules} == {"phoneme"}
    assert {rule.alphabet for rule in rules} == {"ipa"}


def test_alias_payload_shape():
    assert Rule("CpG", "alias", "see pee gee").as_payload() == {
        "string_to_replace": "CpG",
        "type": "alias",
        "alias": "see pee gee",
    }


def test_phoneme_payload_carries_the_alphabet():
    payload = Rule("SNP", "phoneme", "sn\u026ap").as_payload()
    assert payload == {
        "string_to_replace": "SNP",
        "type": "phoneme",
        "phoneme": "sn\u026ap",
        "alphabet": "ipa",
    }


def test_coverage_matches_whole_tokens_only():
    rules = [Rule("CI", "alias", "confidence interval"), Rule("CpG", "alias", "see pee gee")]
    hits = coverage("Science reports a 95% CI for each CpG site.", rules)
    assert [rule.string_to_replace for rule in hits] == ["CI", "CpG"]

    assert coverage("Scientific CpGs", [Rule("CI", "alias", "x")]) == []


def test_coverage_on_a_real_abstract_finds_domain_terms(record):
    hits = coverage(record.abstract, rules_from_pls(ALIAS_LEXICON))
    found = {rule.string_to_replace for rule in hits}
    assert {"EWAS", "Infinium", "450k"} <= found


def test_write_pls_round_trips(tmp_path):
    original = [Rule("CpG", "alias", "see pee gee"), Rule("SNP", "phoneme", "sn\u026ap")]
    path = write_pls(original, tmp_path / "out.pls")
    assert load_pls(path) == original


def test_write_pls_escapes_markup(tmp_path):
    path = write_pls([Rule("R&D", "alias", "R and D")], tmp_path / "amp.pls")
    assert "&amp;" in path.read_text()
    assert load_pls(path)[0].string_to_replace == "R&D"


def test_malformed_lexicon_names_the_file(tmp_path):
    bad = tmp_path / "bad.pls"
    bad.write_text("<lexicon><lexeme>")
    with pytest.raises(InvalidLexicon, match="bad.pls"):
        load_pls(bad)


def test_empty_lexicon_is_rejected(tmp_path):
    empty = tmp_path / "empty.pls"
    empty.write_text('<?xml version="1.0"?><lexicon version="1.0"/>')
    with pytest.raises(InvalidLexicon, match="no usable lexemes"):
        load_pls(empty)


def test_bundled_lexicons_ship_inside_the_wheel():
    for name in (ALIAS_LEXICON, PHONEME_LEXICON):
        assert lexicon_path(name).is_file()
