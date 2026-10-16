# Teaching a voice model to say "CpG"

### A practical guide to ElevenLabs pronunciation dictionaries

**Time:** about 30 minutes. **Cost:** a few hundred characters of quota.
**You need:** Python 3.10+, an [ElevenLabs API key](https://elevenlabs.io/app/settings/api-keys), and a terminal.

By the end you will be able to:

- Explain why text-to-speech on technical writing fails, and which half of the problem belongs to text normalisation rather than to the voice model
- Write a W3C PLS lexicon and upload it with `add-from-file`
- Attach a dictionary to a speech request with `pronunciation_dictionary_locators`
- Choose between `alias` and `phoneme` rules, and predict which models will accept each
- Debug the three failures that catch everyone the first time

Everything below is implemented in [audio-abstracts](https://github.com/kkamieniecka/audio-abstracts); you can read the finished version at any point, but the interesting parts are the detours.

---

## Why this is worth your time

I work on epigenomics pipelines. A colleague with dyslexia asked whether she could *listen* to the week's preprints instead of reading them, the way she listens to audiobooks. The answer should obviously be yes — the models are good enough, and the abstracts are already machine-readable.

The first attempt was unusable. Not because the voice was bad; the voice was excellent. It was because the first sentence came out as:

> "Epigenome-wide association studies, cupig islands, measured on the grutch thirty-eight assembly…"

Three domain terms, three mispronunciations, and she had stopped listening. This is a solved problem, but the solution is in a corner of the API that general tutorials skip. Here it is.

---

## Step 1 — Fix the text before you touch the voice

This is the step everyone skips, and skipping it means you spend the afternoon blaming the model for things it was never given a chance to get right.

Pull an abstract from Europe PMC — no key, no registration:

```bash
curl -s 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1101/553784&resultType=core&format=json' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["resultList"]["result"][0]["abstractText"][:300])'
```

```
<h4>Background</h4>  Epigenome-wide association studies (EWAS) analyse genome-wide
activity of epigenetic marks in cohorts of different individuals...
```

Note what is already wrong for speech, before any model is involved. There is an `<h4>` tag. Structured abstracts carry section headings as markup; send them raw and you get the literal string "h4 Background h4" or, worse, silence where a pause should be. There will be bracketed citations like `[1,2]`, symbols (`±`, `≥`, `μM`, `37°C`, `p < 0.05`) that are either skipped or read as punctuation names, and bare URLs — `http://galaxyproject.org` spoken character by character is thirty seconds of nobody's life well spent.

So the first module in the pipeline is a normaliser. Strip the markup, convert `<h4>Background</h4>` into the sentence `Background.` so the model takes a breath, delete citations and URLs, and vocalise the symbols:

```python
(r"\u00b1",            " plus or minus "),
(r"(?<=\d)\s*%",       " percent"),
(r"\u00b0\s?C\b",      " degrees Celsius"),
(r"(?<=\d)\s*-\s*(?=\d)", " to "),      # "450-850" -> "450 to 850"
(r"\bet\s+al\.",       "and colleagues"),
```

> **A detour worth having.** My rule for `/` was `(r"\s*/\s*(?=[a-zA-Z])", " or ")`, intended for "cases/controls". It turned `http://galaxyproject.org` into "http:/ or galaxyproject.org". The fix was to strip URLs *before* the symbol pass and to require a letter on both sides of the slash. I only noticed because a test asserted on a real abstract rather than on a sentence I had invented. Fixture-driven tests earn their keep on exactly this class of bug.

What does **not** belong here is vocabulary. It is tempting to add `text.replace("CpG", "see pee gee")` and move on. Don't: that fix only works inside your script, cannot be reviewed by a domain expert who does not read Python, and has to be rewritten for every project. Vocabulary belongs in a dictionary, which is the rest of this tutorial.

```bash
audio-abstracts script 10.1101/553784
```

---

## Step 2 — Synthesise once, badly, on purpose

Send the cleaned script with no dictionary at all. You want to *hear* the baseline, both because it is motivating and because you need something to compare against.

```python
import os, requests

text = open("script.txt").read()
response = requests.post(
    "https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb",
    headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
    params={"output_format": "mp3_44100_128"},
    json={"text": text, "model_id": "eleven_v3"},
    timeout=120,
)
response.raise_for_status()
open("before.mp3", "wb").write(response.content)
```

Three things to notice in that request. The key goes in an `xi-api-key` header, not `Authorization: Bearer`. The `output_format` is a **query parameter**, not a body field — a surprisingly common source of "why is my audio still 44.1 kHz". And the voice in the URL path (`JBFqnCBsd6RMkjVDRZzb`) is George, one of the documented default voices; `GET /v1/voices` lists the ones your key can use.

Listen to `before.mp3`. Keep it.

---

## Step 3 — Write the lexicon

The dictionary format is [PLS](https://www.w3.org/TR/pronunciation-lexicon/), a W3C standard. You could POST rules as JSON instead, and for two or three terms you should. For a vocabulary you intend to maintain, use the file: it diffs cleanly in a pull request, a colleague can review it without reading any code, and it is not specific to one vendor.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<lexicon version="1.0"
         xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"
         alphabet="ipa" xml:lang="en-GB">
  <lexeme><grapheme>CpG</grapheme><alias>see pee gee</alias></lexeme>
  <lexeme><grapheme>GWAS</grapheme><alias>gee-wass</alias></lexeme>
  <lexeme><grapheme>SNP</grapheme><alias>snip</alias></lexeme>
  <lexeme><grapheme>GRCh38</grapheme><alias>gee-arr-see-aitch thirty-eight</alias></lexeme>
</lexicon>
```

An **alias rule** is a literal string replacement applied before synthesis. You are not describing the sound; you are rewriting the text into something the model already pronounces correctly. Write the alias the way a researcher says the term out loud — `snip`, not `S-N-P` — and read it back to yourself to check.

Two properties of alias matching that are not obvious and will bite you:

- **It is case-sensitive.** My lexicon had `450K`; the paper I tested on wrote `450k`. The dictionary uploaded fine, the request succeeded, and nothing changed in the audio. Both spellings now ship.
- **It is substring-based.** A rule for `CpG` also fixes `CpGs`, which is convenient. It also means `CI` → "confidence interval" would fire inside other words if the API matched naively; test your short acronyms specifically.

> **XML trap:** a comment containing `--` is not well-formed XML. If your `add-from-file` upload is rejected before the API has looked at a single rule, run the file through a parser first. I lost ten minutes to a comment reading "spelled phonetically, not the way it is written".

---

## Step 4 — Upload it, and keep both halves of the answer

```python
with open("life-science.pls", "rb") as handle:
    created = requests.post(
        "https://api.elevenlabs.io/v1/pronunciation-dictionaries/add-from-file",
        headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
        files={"file": ("life-science.pls", handle, "application/xml")},
        data={"name": "life-science vocabulary"},
        timeout=60,
    ).json()

print(created["id"], created["version_id"])
```

Multipart, not JSON — the PLS file is uploaded as `file`, with the name as a form field alongside it.

The response gives you **two** identifiers and you need both. `id` names the dictionary; `version_id` names the current contents of it. Adding rules later with `POST /v1/pronunciation-dictionaries/{id}/add-rules` returns a *new* `version_id`, and a speech request quoting the old one quietly uses the old rules. No error, no warning, just an afternoon wondering why your new term is still mispronounced. Store the pair together:

```python
@dataclass(frozen=True)
class DictionaryRef:
    pronunciation_dictionary_id: str
    version_id: str
```

While you are here: a dictionary is a durable server-side resource, and nothing stops you uploading a fresh duplicate every time your script runs. Key a small local cache on the SHA-256 of the lexicon file. Edit the file and it re-uploads; leave it alone and it does not.

---

## Step 5 — Attach it to the speech request

```python
json={
    "text": text,
    "model_id": "eleven_v3",
    "pronunciation_dictionary_locators": [
        {
            "pronunciation_dictionary_id": created["id"],
            "version_id": created["version_id"],
        }
    ],
}
```

Dictionaries are applied **in the order given**, and there is a cap of three per request. Both facts matter if you are layering, say, a general life-science lexicon under a project-specific one: put the specific one where it wins, and validate the count client-side rather than discovering the cap as a 422.

Synthesise again, call it `after.mp3`, and play the two back to back. This A/B is the whole demo — it is also, incidentally, the single best thing to put in a conference talk, because the audience hears the problem and the fix in fifteen seconds without you explaining either.

---

## Step 6 — Phoneme rules, and the model compatibility rule

Alias spelling has a ceiling. You can respell *Illumina* as `ill-oo-mee-na` and still land the stress wrong, because you are only choosing letters, not prosody. For those cases there are **phoneme rules**, which take an IPA or CMU Arpabet transcription directly:

```xml
<lexeme><grapheme>Illumina</grapheme><phoneme>ɪljuːˈmiːnə</phoneme></lexeme>
<lexeme><grapheme>epigenome</grapheme><phoneme>ˌɛpɪˈdʒiːnəʊm</phoneme></lexeme>
```

Here is the part that costs people an afternoon:

| Rule type | Model support | Failure mode if unsupported |
| --- | --- | --- |
| `alias` | Every text-to-speech model | — |
| `phoneme` | A subset of models only | Request **rejected**, not silently ignored |

A dictionary that works perfectly on one model will fail on another, and the rejection does not always explain itself. Three defences, in increasing order of usefulness:

- Keep phoneme rules in a **separate file** from alias rules, so a model switch degrades to "slightly worse stress" rather than "every request fails"
- Check the model against a known-good list **before** spending the request, and say which models would work in the error message
- Do not trust your own list. Model availability moves; ask the API. `audio-abstracts doctor --model <id>` checks that the model exists for your key and, given a phoneme dictionary, probes whether it is accepted

The general principle: reach for IPA only where respelling genuinely cannot carry the stress. In my lexicon that is sixteen terms out of sixty-seven. The other fifty-one are alias rules, and they work everywhere.

---

## Step 7 — Make it testable without a key

If a contributor has to sign up for an API key before `pytest` passes, most of them will not. Two moves fix this.

**Inject the transport.** Give the client a `session` parameter and default it to a fresh `requests.Session()`. In tests, pass a stub that records the call and replays a canned response. Now you can assert on the request itself:

```python
def test_locators_are_sent_as_id_and_version_pairs():
    session = StubSession(StubResponse(content=b""))
    client = ElevenLabsClient(api_key="k", session=session)
    client.text_to_speech("x", dictionaries=[DictionaryRef("dict1", "ver1")])

    assert session.last["json"]["pronunciation_dictionary_locators"] == [
        {"pronunciation_dictionary_id": "dict1", "version_id": "ver1"}
    ]
```

**Add a dry run.** A `dry_run=True` flag that builds the request and returns it instead of sending it, with the key replaced by `$ELEVENLABS_API_KEY`, gives you a `--dry-run` CLI flag that prints copy-pasteable curl. It is a debugging aid, a documentation generator, and a way for someone to evaluate your tool before spending a credit — three jobs for about twenty lines.

Capture a real API response as a fixture once, commit it, and test against that. It is how I found the `450k` casing bug and the URL bug: invented test sentences are too clean to catch anything.

---

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `401` | Key missing, revoked, or mistyped | Check `ELEVENLABS_API_KEY` is exported in *this* shell |
| `404` naming a voice | Voice not in your library | `GET /v1/voices` and copy the id |
| `422` mentioning pronunciation | Phoneme rules on a model that does not take them | Switch model, or convert the rules to aliases |
| `422` on upload, before rules are read | Malformed PLS | Parse the file locally; check for `--` in comments |
| `429` | Rate limit or concurrency cap | Back off and retry; batch your requests |
| Request succeeds, audio unchanged | Stale `version_id`, or the term never matched | Re-check the version after `add-rules`; remember matching is case-sensitive |
| Audio is correct but reads out URLs and citations | Normalisation skipped | See Step 1 — this is not a model problem |

---

## Where to take it next

The lexicon is the reusable part. Sixty-seven life-science terms are in the repo, but the same thirty minutes buys you a chemistry lexicon, a clinical-trials lexicon, or a lexicon of your own company's product names and customer names — which is the version of this problem that most teams actually have. Agents, in particular, mispronounce exactly the words a customer most expects you to get right: their own name, and yours.

If you build one, send a pull request. Vocabulary is the kind of thing that is tedious to write once and free to share forever.

---

*Code: [github.com/kkamieniecka/audio-abstracts](https://github.com/kkamieniecka/audio-abstracts) — MIT licensed, including the lexicons.*
