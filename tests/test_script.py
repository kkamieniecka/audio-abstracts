from audio_abstracts.script import build_script, chunk, normalise


def test_structured_headings_become_spoken_sentences():
    out = normalise("<h4>Background</h4> Epigenome-wide studies are common.")
    assert out.startswith("Background. Epigenome-wide")
    assert "<" not in out


def test_markup_entities_and_citations_are_removed():
    out = normalise("Methylation &amp; ageing [1,2] are linked [3-5].")
    assert out == "Methylation and ageing are linked."


def test_symbols_are_vocalised():
    out = normalise("Coverage was 12.4% \u00b1 1.1 at \u226530 \u00d7 depth, 5 \u00b5M, 37\u00b0C.")
    assert "percent" in out
    assert "plus or minus" in out
    assert "greater than or equal to" in out
    assert "microM" in out
    assert "degrees Celsius" in out


def test_numeric_ranges_and_inequalities_are_read_as_words():
    assert "450 to 850" in normalise("450-850 thousand probes")
    assert "less than 0.05" in normalise("p < 0.05")


def test_latin_abbreviations_are_expanded():
    out = normalise("Murat et al. showed this, e.g. in blood, i.e. whole blood.")
    assert "and colleagues" in out
    assert "for example" in out
    assert "that is" in out
    assert "al." not in out


def test_build_script_opens_with_a_spoken_citation(record):
    script = build_script(record)
    lines = script.split("\n\n")
    assert lines[0].startswith("EWAS-Galaxy")
    assert "Murat and colleagues" in lines[1]
    assert "2019" in lines[1]
    assert "Background." in script


def test_build_script_can_omit_the_citation(record):
    assert not build_script(record, include_citation=False).startswith("EWAS-Galaxy")


def test_chunk_splits_on_paragraph_boundaries_only():
    script = "\n\n".join(["sentence one.", "sentence two.", "sentence three."])
    pieces = chunk(script, limit=20)
    assert pieces == ["sentence one.", "sentence two.", "sentence three."]
    assert all(len(p) <= 20 for p in pieces)


def test_chunk_returns_single_piece_when_it_fits(record):
    assert len(chunk(build_script(record))) == 1


def test_urls_are_dropped_rather_than_spelled_out():
    out = normalise("Available from Galaxy (http://galaxyproject.org), a web platform.")
    assert "galaxyproject" not in out
    assert " or " not in out, "the slash rule must not fire inside a URL"
    assert out == "Available from Galaxy, a web platform."


def test_slash_between_words_still_becomes_or():
    assert "cases or controls" in normalise("cases/controls were matched")
