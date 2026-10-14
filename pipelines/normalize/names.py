"""Name normalization (PRD Section 7.3) and romanization variants for village search.

norm = normalize_name("Govt. H.P.S. Doddaballapura", cfg.abbreviations)
norm.norm_name   -> "government higher primary school doddaballapura"
norm.key_tokens  -> ["doddaballapura"]
phonetic_key("Doddaballapura") == phonetic_key("Dodballapur")  -> True
"""

import re
import unicodedata
from dataclasses import dataclass

from indic_transliteration import sanscript

# Unicode block start -> indic_transliteration scheme
_SCRIPTS = [
    (0x0900, sanscript.DEVANAGARI),
    (0x0980, sanscript.BENGALI),
    (0x0A00, sanscript.GURMUKHI),
    (0x0A80, sanscript.GUJARATI),
    (0x0B00, sanscript.ORIYA),
    (0x0B80, sanscript.TAMIL),
    (0x0C00, sanscript.TELUGU),
    (0x0C80, sanscript.KANNADA),
    (0x0D00, sanscript.MALAYALAM),
]


@dataclass(frozen=True)
class NormalizedName:
    display: str
    norm_name: str
    key_tokens: list[str]


def detect_script(text: str) -> str | None:
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp < 0x0D80:
            for start, scheme in reversed(_SCRIPTS):
                if cp >= start:
                    return scheme
    return None


def to_latin(text: str) -> str:
    """Transliterate Indic-script text to ITRANS-style Latin; Latin text passes through."""
    scheme = detect_script(text)
    if scheme:
        text = sanscript.transliterate(text, scheme, sanscript.ITRANS)
    # strip accents (e.g. IAST input) and ITRANS markers such as "~" and "."
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def basic_clean(text: str) -> str:
    """Lower-case Latin text with punctuation removed and spaces collapsed."""
    text = to_latin(text).lower()
    text = re.sub(r"\b(?:[a-z]\.){2,}", lambda m: m.group(0).replace(".", ""), text)  # g.p.s.
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def normalize_name(name: str, dictionaries=None, extra_generic=()) -> NormalizedName:
    """Full normalization: clean, expand abbreviations, unify spellings, pick key tokens.

    dictionaries is the abbreviations config (pipelines.config.AbbreviationsFile) or None.
    extra_generic: further tokens to drop from key_tokens (for example the village name).
    """
    tokens = basic_clean(name).split()
    if dictionaries is not None:
        expanded = []
        spell = dictionaries.spelling_variants
        for tok in tokens:
            tok = spell.get(tok, tok)
            expanded.extend(
                spell.get(t, t) for t in dictionaries.abbreviations.get(tok, tok).split()
            )
        tokens = expanded
        generic = set(dictionaries.generic_tokens)
    else:
        generic = set()
    generic |= {basic_clean(t) for t in extra_generic}
    key = [t for t in tokens if t not in generic]
    return NormalizedName(
        display=" ".join(name.split()), norm_name=" ".join(tokens), key_tokens=key
    )


# Romanization of Indian place names varies a lot (Doddaballapura / Dodballapur /
# Doddaballapur). phonetic_key maps such spellings to one skeleton so search can match them.
_SUFFIXES = [
    (r"(halli|hally|hali|halle)$", "hali"),
    (r"(puram|pura|pur)$", "pur"),
    (r"(palyam|palya|palaya|palayam)$", "paly"),
    (r"(nagara|nagar|nagaram)$", "nagar"),
    (r"(ooru|uru|ur)$", "ur"),
    (r"(kere|kare)$", "kere"),
    (r"(gere|gare)$", "gere"),
    (r"(hosur|hosuru)$", "hosur"),
]
_DIGRAPHS = [
    ("aa", "a"),
    ("ee", "i"),
    ("ii", "i"),
    ("oo", "u"),
    ("uu", "u"),
    ("w", "v"),
    ("z", "j"),
    ("ph", "f"),
    ("sh", "s"),
    ("th", "t"),
    ("dh", "d"),
    ("bh", "b"),
    ("kh", "k"),
    ("gh", "g"),
    ("ch", "c"),
    ("jh", "j"),
    ("y", "i"),
]


def phonetic_key(name: str) -> str:
    """Spelling-insensitive skeleton of a (village) name, spaces removed."""
    key = basic_clean(name).replace(" ", "")
    for pattern, repl in _SUFFIXES:
        key = re.sub(pattern, repl, key)
    for a, b in _DIGRAPHS:
        key = key.replace(a, b)
    key = re.sub(r"(.)\1+", r"\1", key)  # doubled letters
    if len(key) > 4:
        key = re.sub(r"(?<=[^aeiou])a(?=[^aeiou]|$)", "", key)  # weak 'a' between consonants
    return key


def village_variants(name: str) -> list[str]:
    """Search variants stored in village.name_variants: cleaned name, joined form, phonetic key."""
    clean = basic_clean(name)
    variants = [clean, clean.replace(" ", ""), phonetic_key(clean)]
    return list(dict.fromkeys(v for v in variants if v))
