import pytest

from pipelines.config import load_file
from pipelines.normalize.names import (
    basic_clean,
    normalize_name,
    phonetic_key,
    to_latin,
    village_variants,
)

ABBR = load_file("abbreviations")


def test_basic_clean():
    assert basic_clean("  Govt. H.P.S., Doddaballapura ") == "govt hps doddaballapura"
    assert basic_clean("G.P.S. Kodigehalli") == "gps kodigehalli"
    assert basic_clean("Sri Rama-Temple (Old)") == "sri rama temple old"


def test_kannada_and_devanagari_to_latin():
    assert basic_clean(to_latin("ದೊಡ್ಡಬಳ್ಳಾಪುರ")) == "doddaballapura"
    assert basic_clean("राजकीय विद्यालय") == "rajakiya vidyalaya"


@pytest.mark.parametrize(
    "raw, norm, key",
    [
        (
            "Govt. H.P.S. Kodigehalli",
            "government higher primary school kodigehalli",
            ["kodigehalli"],
        ),
        ("GLPS Hosahalli", "government lower primary school hosahalli", ["hosahalli"]),
        ("PHC Sasalu", "primary health center sasalu", ["primary", "sasalu"][1:]),
        ("Anganawadi Centre - 2", "anganwadi center 2", ["anganwadi", "2"]),
        ("Rajkeeya Prathmik Vidhyalay", "rajkiya prathamik vidyalaya", ["rajkiya", "prathamik"]),
    ],
)
def test_normalize_name(raw, norm, key):
    result = normalize_name(raw, ABBR)
    assert result.norm_name == norm
    assert result.key_tokens == key


def test_village_name_removed_from_key_tokens():
    result = normalize_name("GHPS Kodigehalli", ABBR, extra_generic=["Kodigehalli"])
    assert result.key_tokens == []


@pytest.mark.parametrize(
    "a, b",
    [
        ("Doddaballapura", "Dodballapur"),
        ("Doddaballapura", "Doddaballapur"),
        ("Kodigehalli", "Kodigehally"),
        ("Devanahalli", "Dévanahalli"),
        ("Hoskote", "Hosakote"),
        ("Nelamangala", "Nelamangla"),
        ("Bashettihalli", "Bashettyhalli"),
        ("Thubagere", "Tubagere"),
        ("Rajanukunte", "Raajanukunte"),
        ("Madhure", "Madure"),
    ],
)
def test_phonetic_key_matches_spelling_variants(a, b):
    assert phonetic_key(a) == phonetic_key(b)


@pytest.mark.parametrize("a, b", [("Kodigehalli", "Kadigenahalli"), ("Sasalu", "Sulibele")])
def test_phonetic_key_keeps_different_names_apart(a, b):
    assert phonetic_key(a) != phonetic_key(b)


def test_village_variants():
    v = village_variants("Aluru Duddanahalli")
    assert v[0] == "aluru duddanahalli"
    assert "alurududdanahalli" in v
    assert phonetic_key("Alurududdanahalli") in v
