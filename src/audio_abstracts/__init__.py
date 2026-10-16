"""Turn a paper's abstract into listenable audio with ElevenLabs.

The point of this package is not text-to-speech in general -- it is the
*domain vocabulary* problem. A model that reads "CpG" as "cupig" and
"GRCh38" as "grutch thirty-eight" is unusable for scientific content, no
matter how good the voice is. Pronunciation dictionaries fix that, and
this package is a worked example of using them properly.
"""

__version__ = "0.1.0"

from .client import DEFAULT_MODEL, DEFAULT_VOICE, PHONEME_RULE_MODELS, ElevenLabsClient
from .europepmc import Record, fetch_record
from .lexicon import Rule, coverage, load_pls, rules_from_pls
from .script import build_script

__all__ = [
    "Record",
    "fetch_record",
    "build_script",
    "Rule",
    "load_pls",
    "rules_from_pls",
    "coverage",
    "ElevenLabsClient",
    "PHONEME_RULE_MODELS",
    "DEFAULT_MODEL",
    "DEFAULT_VOICE",
]
