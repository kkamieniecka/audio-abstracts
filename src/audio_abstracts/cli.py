"""Command line interface.

Subcommands are ordered by how much they cost you: `script` and `lexicon`
need no key at all, `voices`/`models`/`doctor` are free metadata calls,
and only `speak` consumes credits.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .cache import fingerprint, lookup, remember
from .client import (
    DEFAULT_MODEL,
    DEFAULT_VOICE,
    PHONEME_RULE_MODELS,
    DictionaryRef,
    ElevenLabsClient,
    ElevenLabsError,
    Prepared,
)
from .europepmc import NotFound, fetch_record
from .lexicon import (
    ALIAS_LEXICON,
    PHONEME_LEXICON,
    coverage,
    lexicon_path,
    load_pls,
)
from .script import build_script, chunk

ENV_KEY = "ELEVENLABS_API_KEY"


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except NotFound as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except ElevenLabsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


# -- subcommands ----------------------------------------------------------


def cmd_script(args: argparse.Namespace) -> int:
    """Print the narration script. No API key, no credits, no excuses."""
    record = fetch_record(args.identifier)
    script = build_script(record, include_citation=not args.no_citation)
    print(script)
    if args.show_coverage:
        rules = load_pls(lexicon_path(ALIAS_LEXICON))
        hits = coverage(script, rules)
        print(
            f"\n--- {len(hits)} of {len(rules)} dictionary terms occur in this text ---",
            file=sys.stderr,
        )
        for rule in hits:
            print(f"  {rule.string_to_replace} -> {rule.value}", file=sys.stderr)
    return 0


def cmd_lexicon(args: argparse.Namespace) -> int:
    """Show the bundled rules, optionally filtered to a given text."""
    path = lexicon_path(PHONEME_LEXICON if args.phonemes else ALIAS_LEXICON)
    rules = load_pls(path)
    if args.against:
        text = Path(args.against).read_text(encoding="utf-8")
        rules = coverage(text, rules)
    print(f"# {path.name} ({len(rules)} rules)")
    for rule in rules:
        print(f"{rule.string_to_replace}\t{rule.type}\t{rule.value}")
    return 0


def cmd_voices(args: argparse.Namespace) -> int:
    client = _client(args)
    for voice in client.list_voices():
        labels = voice.get("labels") or {}
        descriptors = ", ".join(
            str(labels[k]) for k in ("accent", "gender", "use_case") if labels.get(k)
        )
        print(f"{voice.get('voice_id', '?'):24}  {voice.get('name', '?'):22}  {descriptors}")
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    client = _client(args)
    for model in client.list_models():
        model_id = model.get("model_id", "?")
        phoneme = "yes" if model_id in PHONEME_RULE_MODELS else "alias only"
        print(f"{model_id:26}  phoneme rules: {phoneme:10}  {model.get('name', '')}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Check the key, then ask the API whether a model takes phoneme rules.

    The compatibility table in the README is a snapshot. This asks.
    """
    client = _client(args)
    print(f"key: reading {ENV_KEY} ... {'set' if client.api_key else 'MISSING'}")
    models = {m.get("model_id") for m in client.list_models()}
    print(f"models visible to this key: {len(models)}")
    if args.model not in models:
        print(f"model {args.model!r} is NOT available to this key")
        return 2
    print(f"model {args.model!r}: available")

    probe = DictionaryRef(args.dictionary_id, args.version_id) if args.dictionary_id else None
    if probe is None:
        print(
            "phoneme probe: skipped (pass --dictionary-id/--version-id from a "
            "phoneme dictionary to test acceptance)"
        )
        return 0
    try:
        client.text_to_speech("CpG", voice_id=args.voice, model_id=args.model, dictionaries=[probe])
    except ElevenLabsError as exc:
        print(f"phoneme probe: REJECTED ({exc.status_code}) -- use alias rules here")
        return 2
    print("phoneme probe: accepted")
    return 0


def cmd_speak(args: argparse.Namespace) -> int:
    """The whole pipeline: fetch, normalise, upload rules, synthesise."""
    record = fetch_record(args.identifier)
    script = build_script(record, include_citation=not args.no_citation)
    pieces = chunk(script)

    client = _client(args)
    dictionaries: list[DictionaryRef] = []
    if not args.no_dictionary:
        dictionaries.append(_ensure_dictionary(client, ALIAS_LEXICON, args))
    if args.phonemes:
        if args.model not in PHONEME_RULE_MODELS:
            print(
                f"error: model {args.model!r} does not honour phoneme rules. "
                f"Choose one of {sorted(PHONEME_RULE_MODELS)}, or drop --phonemes "
                "and rely on the alias lexicon, which every model supports.",
                file=sys.stderr,
            )
            return 2
        dictionaries.append(_ensure_dictionary(client, PHONEME_LEXICON, args))

    audio = bytearray()
    for index, piece in enumerate(pieces, start=1):
        result = client.text_to_speech(
            piece,
            voice_id=args.voice,
            model_id=args.model,
            output_format=args.format,
            dictionaries=dictionaries,
        )
        if isinstance(result, Prepared):
            print(f"# request {index} of {len(pieces)}")
            print(result.as_curl())
            print()
            continue
        audio.extend(result)
        print(f"synthesised {index}/{len(pieces)} ({len(piece)} characters)", file=sys.stderr)

    if args.dry_run:
        return 0

    out = Path(args.out or _default_name(record, args.format))
    out.write_bytes(bytes(audio))
    print(f"wrote {out} ({len(audio) / 1024:.0f} KiB)")
    return 0


# -- helpers --------------------------------------------------------------


def _client(args: argparse.Namespace) -> ElevenLabsClient:
    return ElevenLabsClient(
        api_key=os.environ.get(ENV_KEY),
        dry_run=getattr(args, "dry_run", False),
    )


def _ensure_dictionary(
    client: ElevenLabsClient, lexicon_name: str, args: argparse.Namespace
) -> DictionaryRef:
    """Upload a lexicon unless an identical one was uploaded before."""
    path = lexicon_path(lexicon_name)
    key = f"{lexicon_name}:{fingerprint(path)}"
    cached = None if args.refresh_dictionary else lookup(key)
    if cached:
        print(f"dictionary {lexicon_name}: reusing {cached.version_id}", file=sys.stderr)
        return cached
    ref = client.create_dictionary_from_file(
        path,
        name=f"audio-abstracts {lexicon_name}",
        description="Life-science vocabulary for read-aloud abstracts",
    )
    if client.dry_run:
        # A dry run never uploaded anything, so its placeholder ids must
        # not poison the cache for the next real run.
        print(f"dictionary {lexicon_name}: would upload {path.name}", file=sys.stderr)
        return ref
    remember(key, ref)
    print(f"dictionary {lexicon_name}: uploaded {ref.version_id}", file=sys.stderr)
    return ref


def _default_name(record, output_format: str) -> str:
    stem = (record.doi or record.id or "abstract").replace("/", "_")
    suffix = "mp3" if output_format.startswith("mp3") else "pcm"
    return f"{stem}.{suffix}"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audio-abstracts",
        description="Read a paper's abstract aloud, with the jargon pronounced correctly.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    script_parser = subparsers.add_parser(
        "script", help="print the narration script (no API key needed)"
    )
    script_parser.add_argument("identifier", help="DOI, PMID, PMCID or title")
    script_parser.add_argument("--no-citation", action="store_true")
    script_parser.add_argument(
        "--show-coverage",
        action="store_true",
        help="list which dictionary terms occur in this abstract",
    )
    script_parser.set_defaults(handler=cmd_script)

    lexicon_parser = subparsers.add_parser("lexicon", help="show the bundled rules")
    lexicon_parser.add_argument("--phonemes", action="store_true")
    lexicon_parser.add_argument("--against", metavar="FILE", help="filter to terms in FILE")
    lexicon_parser.set_defaults(handler=cmd_lexicon)

    voices_parser = subparsers.add_parser("voices", help="list voices for your key")
    voices_parser.set_defaults(handler=cmd_voices)

    models_parser = subparsers.add_parser("models", help="list models and rule support")
    models_parser.set_defaults(handler=cmd_models)

    doctor_parser = subparsers.add_parser(
        "doctor", help="check key, model availability and phoneme-rule acceptance"
    )
    doctor_parser.add_argument("--model", default=DEFAULT_MODEL)
    doctor_parser.add_argument("--voice", default=DEFAULT_VOICE)
    doctor_parser.add_argument("--dictionary-id")
    doctor_parser.add_argument("--version-id")
    doctor_parser.set_defaults(handler=cmd_doctor)

    speak_parser = subparsers.add_parser("speak", help="synthesise an abstract to audio")
    speak_parser.add_argument("identifier", help="DOI, PMID, PMCID or title")
    speak_parser.add_argument("-o", "--out", help="output path (default: <doi>.mp3)")
    speak_parser.add_argument("--voice", default=DEFAULT_VOICE)
    speak_parser.add_argument("--model", default=DEFAULT_MODEL)
    speak_parser.add_argument("--format", default="mp3_44100_128")
    speak_parser.add_argument("--no-citation", action="store_true")
    speak_parser.add_argument(
        "--no-dictionary", action="store_true", help="synthesise without any rules"
    )
    speak_parser.add_argument(
        "--phonemes",
        action="store_true",
        help="also apply the IPA phoneme lexicon (compatible models only)",
    )
    speak_parser.add_argument("--refresh-dictionary", action="store_true")
    speak_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the curl equivalent of every request instead of sending it",
    )
    speak_parser.set_defaults(handler=cmd_speak)

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
