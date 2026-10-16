# audio-abstracts

Read a research paper's abstract aloud with the [ElevenLabs API](https://elevenlabs.io/docs/api-reference/introduction) — and get the jargon right.

[![ci](https://github.com/kkamieniecka/audio-abstracts/actions/workflows/ci.yml/badge.svg)](https://github.com/kkamieniecka/audio-abstracts/actions/workflows/ci.yml)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

Text-to-speech on scientific writing fails for a reason that has nothing to do with voice quality. The voice is excellent. It just says *cupig* for `CpG`, *grutch thirty-eight* for `GRCh38`, and stresses *Illumina* on the wrong syllable. One mangled gene symbol in the first ten seconds and a researcher closes the tab.

This is a small, complete worked example of fixing that with **pronunciation dictionaries**, built around a pipeline anyone in the life sciences can run on their own papers.

---

## The problem, concretely

| Written in the paper | What a model reads without a dictionary | What this repo makes it say |
| --- | --- | --- |
| `CpG` | "cupig" | see pee gee |
| `GRCh38` | "grutch thirty-eight" | gee-arr-see-aitch thirty-eight |
| `SNP` | "ess en pee" | snip |
| `GWAS` | "gee-double-you-ay-ess" | gee-wass |
| `minfi` | "min-fye" | min-fee |
| `in vivo` | "in VY-voh" | in vee-voh |

Sixty-seven rules ship in [`life-science.pls`](src/audio_abstracts/data/life-science.pls). They are a W3C [PLS](https://www.w3.org/TR/pronunciation-lexicon/) lexicon, which means they are diffable in version control, reviewable by a domain expert who has never touched an API, and portable to other speech engines.

## Quickstart

The first step needs no API key, so you can see what the tool does before signing up for anything.

```bash
pip install git+https://github.com/kkamieniecka/audio-abstracts
audio-abstracts script 10.1101/553784 --show-coverage
```

```
EWAS-Galaxy: a tools suite for population epigenetics integrated into Galaxy.

Murat and colleagues in a preprint in 2019.

Background. Epigenome-wide association studies (EWAS) analyse genome-wide
activity of epigenetic marks in cohorts of different individuals to find
associations between epigenetic variation and phenotype. ...

--- 3 of 67 dictionary terms occur in this text ---
  EWAS -> ee-wass
  Infinium -> in-finny-um
  450k -> four-fifty-kay
```

The running example throughout this repository is [EWAS-Galaxy](https://doi.org/10.1101/553784), which I wrote and published as first author under my maiden name, Katarzyna Murat. Without a dictionary, the model cannot say its title.

Then add a key and synthesise:

```bash
export ELEVENLABS_API_KEY="..."          # https://elevenlabs.io/app/settings/api-keys
audio-abstracts speak 10.1101/553784 -o ewas-galaxy.mp3
```

Not ready to spend credits? `--dry-run` prints the exact request it would send, as copy-pasteable curl:

```bash
audio-abstracts speak 10.1101/553784 --dry-run
```

```
curl -X POST \
  'https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb?output_format=mp3_44100_128' \
  -H 'xi-api-key: $ELEVENLABS_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "EWAS-Galaxy: a tools suite for population epigenetics ...",
  "model_id": "eleven_v3",
  "pronunciation_dictionary_locators": [
    {
      "pronunciation_dictionary_id": "...",
      "version_id": "..."
    }
  ]
}'
```

## How it works

```
  DOI / PMID                                                         MP3
      │                                                               ▲
      ▼                                                               │
┌─────────────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ Europe PMC  │──▶│ normalise    │──▶│ upload PLS      │──▶│ text-to-speech   │
│ (no key)    │   │ the script   │   │ lexicon, cache  │   │ with locators    │
└─────────────┘   └──────────────┘   └─────────────────┘   └──────────────────┘
                  strip markup,       alias rules: all      ≤ 3 dictionaries
                  citations, URLs;    models                per request
                  vocalise symbols    phoneme rules: some
```

Three design decisions are worth calling out, because each one is a mistake I made first:

1. **Fix the text before you fix the voice.** Abstracts are written to be scanned, not spoken. They carry `<h4>` section headings, bracketed citations, bare URLs and inline statistics. [`script.py`](src/audio_abstracts/script.py) handles those; the dictionary handles vocabulary. Mixing the two concerns makes both harder to test.
2. **Alias rules first, phoneme rules only when they earn it.** Alias rules are honoured by every model. Reach for IPA only where respelling genuinely cannot carry the stress — which is roughly sixteen terms, not sixty-seven.
3. **Cache the dictionary.** A dictionary is a durable server-side resource, but nothing stops you creating a duplicate on every run. The cache key is the SHA-256 of the lexicon file, so editing the lexicon re-uploads automatically and leaving it alone does not.

## The compatibility rule that costs people an afternoon

Pronunciation dictionaries come in two flavours, and they do **not** have the same model support:

| Rule type | What it does | Model support |
| --- | --- | --- |
| `alias` | Literal string replacement before synthesis — `CpG` becomes the text "see pee gee" | Every text-to-speech model |
| `phoneme` | IPA or CMU Arpabet transcription applied directly | A subset of models only |

A phoneme rule sent to a model that does not support it is **rejected, not ignored** — so a dictionary that works on one model will 422 on another, and the error does not always say why. This repo handles it in three places: the model list is a single constant (`PHONEME_RULE_MODELS` in [`client.py`](src/audio_abstracts/client.py)), the CLI refuses `--phonemes` on an incompatible model before spending a request, and a 422 mentioning pronunciation is re-raised with the compatible model list attached.

Model availability moves, so rather than trusting the constant, ask:

```bash
audio-abstracts models      # every model your key can see, annotated
audio-abstracts doctor --model eleven_v3
```

## Commands

Ordered by what they cost you. Only `speak` consumes credits.

| Command | Needs a key | Does |
| --- | --- | --- |
| `script <id>` | no | Print the narration script. `--show-coverage` lists which rules apply. |
| `lexicon` | no | Dump the bundled rules. `--phonemes` for the IPA set, `--against FILE` to filter. |
| `voices` | yes (free) | Voices available to your key. |
| `models` | yes (free) | Models, annotated with phoneme-rule support. |
| `doctor` | yes (free) | Check the key, model availability, and whether phoneme rules are accepted. |
| `speak <id>` | yes | The full pipeline. `--dry-run` to see the request without sending it. |

Identifiers can be a DOI, PMID, PMCID, or a free-text title search.

## Testing without an API key

The whole suite runs offline, with no key:

```bash
pip install -e ".[dev]"
pytest          # 39 tests
ruff check src tests
```

Europe PMC responses come from [a fixture](tests/fixtures/ewas_galaxy.json) captured from the live API, and the HTTP client is exercised against a stub session that records the request it was given. That is why CI is green on a fork before the contributor has signed up for anything — and it is also how two real bugs in this repo were caught: `450k` is lowercase in the wild (alias matching is case-sensitive, so both spellings now ship), and an over-eager "/" rule was turning `http://galaxyproject.org` into "http slash or galaxyproject dot org".

## Using the official SDK instead

The package deliberately uses `requests` rather than the [official Python SDK](https://github.com/elevenlabs/elevenlabs-python), so the HTTP surface stays visible, the tests can stub it, and the requests port to any language. For production you want the SDK — it handles retries, streaming and typed models. [`examples/with_sdk.py`](examples/with_sdk.py) is the same pipeline in about a dozen lines of it, so the comparison is one `diff` away.

## Extending the lexicon

Add a `<lexeme>` and re-run — the cache notices the file changed and uploads a new version.

```xml
<lexeme><grapheme>scATAC-seq</grapheme><alias>single-cell ay-tack seek</alias></lexeme>
```

Two things to know. Matching is **case-sensitive and literal**, so `450K` and `450k` are separate rules. And an alias is a *substring* replacement, so a rule for `CpG` also fixes `CpGs` — which is usually what you want, but means you should write the more specific rule first when two overlap.

Pull requests adding vocabulary from other fields are very welcome; chemistry, astronomy and clinical trial reporting all have the same problem.

## What this is not

Not a transcription tool, not a paper summariser, and not a substitute for an author-recorded audio abstract. It reads the abstract you give it, accurately. The scope is deliberately one job, done properly, with the awkward parts documented rather than hidden.

## Further reading

- [TUTORIAL.md](TUTORIAL.md) — build this from scratch in about thirty minutes, including the three places it goes wrong
- [ElevenLabs: pronunciation dictionaries](https://elevenlabs.io/docs/api-reference/pronunciation-dictionaries/create-from-file)
- [W3C Pronunciation Lexicon Specification](https://www.w3.org/TR/pronunciation-lexicon/)
- [Europe PMC REST API](https://europepmc.org/RestfulWebService)

## Licence

MIT. The pronunciation lexicons are MIT too — lift them into your own project.
