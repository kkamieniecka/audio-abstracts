"""The same pipeline in the official Python SDK.

The package itself uses `requests` so that the HTTP surface stays visible
and the tests can stub it. In production you would reach for the official
SDK, which handles retries, streaming and typed models for you. This file
exists so the comparison is one `diff` away.

    pip install "audio-abstracts[sdk]"
    python examples/with_sdk.py 10.1101/553784
"""

from __future__ import annotations

import sys

from elevenlabs import ElevenLabs
from elevenlabs.types import PronunciationDictionaryVersionLocator

from audio_abstracts import build_script, fetch_record
from audio_abstracts.lexicon import ALIAS_LEXICON, lexicon_path


def main(identifier: str, out_path: str = "abstract.mp3") -> None:
    script = build_script(fetch_record(identifier))

    client = ElevenLabs()  # reads ELEVENLABS_API_KEY from the environment

    with lexicon_path(ALIAS_LEXICON).open("rb") as handle:
        dictionary = client.pronunciation_dictionaries.create_from_file(
            file=handle.read(),
            name="life-science vocabulary",
        )

    audio = client.text_to_speech.convert(
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_v3",
        output_format="mp3_44100_128",
        text=script,
        pronunciation_dictionary_locators=[
            PronunciationDictionaryVersionLocator(
                pronunciation_dictionary_id=dictionary.id,
                version_id=dictionary.version_id,
            )
        ],
    )

    with open(out_path, "wb") as handle:
        for chunk in audio:
            handle.write(chunk)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
