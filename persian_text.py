"""Persian/Arabic text normalization for Iran-native search matching.

Deterministic character-level normalization only -- this does not translate meaning, does not
perform linguistically complete transliteration, and knows no real company/product/place
names. It exists so that two differently-typed renderings of the same Persian text (Arabic vs
Persian letterforms, half-space vs full space, Arabic-Indic vs Persian vs Latin digits, alef
variants, optional diacritics) compare equal after normalization -- the same purpose
discovery_pipeline.normalize_entity_name() already serves for Latin text, extended to a script
that simple case-folding cannot handle.
"""

from __future__ import annotations

import re
import unicodedata

_ARABIC_TO_PERSIAN = {
    "ي": "ی",  # Arabic yeh -> Persian yeh
    "ك": "ک",  # Arabic kaf -> Persian kaf
    "ة": "ه",  # teh marbuta -> heh (common informal normalization)
    "ؤ": "و",
    "ئ": "ی",
    "أ": "ا", "إ": "ا", "آ": "ا",  # alef variants -> bare alef
}
_DIGIT_MAP = {
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4", "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
}
_ZERO_WIDTH_NON_JOINER = "‌"
_DIACRITICS = re.compile(r"[ً-ٰٟ]")

_NORMALIZE_TABLE = str.maketrans({**_ARABIC_TO_PERSIAN, **_DIGIT_MAP})


def normalize_persian_text(text: str) -> str:
    """Character-level normalization for comparison/matching, not display."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_NORMALIZE_TABLE)
    text = _DIACRITICS.sub("", text)
    text = text.replace(_ZERO_WIDTH_NON_JOINER, " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


_PERSIAN_TO_LATIN = {
    "ا": "a", "ب": "b", "پ": "p", "ت": "t", "ث": "s", "ج": "j", "چ": "ch", "ح": "h", "خ": "kh",
    "د": "d", "ذ": "z", "ر": "r", "ز": "z", "ژ": "zh", "س": "s", "ش": "sh", "ص": "s", "ض": "z",
    "ط": "t", "ظ": "z", "ع": "a", "غ": "gh", "ف": "f", "ق": "gh", "ک": "k", "گ": "g", "ل": "l",
    "م": "m", "ن": "n", "و": "v", "ه": "h", "ی": "y", " ": " ",
}


def transliterate_persian_heuristic(text: str) -> str:
    """A best-effort, deterministic, systematic Persian->Latin transliteration -- NOT a
    linguistically complete transliteration system (Persian pronunciation is context-dependent
    in ways a fixed character map cannot capture, e.g. و/ی carry multiple values). Useful only
    as one additional query/matching variant among several, never as a canonical identity.
    """
    normalized = normalize_persian_text(text)
    return "".join(_PERSIAN_TO_LATIN.get(ch, ch) for ch in normalized)


_COMPANY_SUFFIXES = (
    "شرکت", "گروه", "صنایع", "بازرگانی", "تجاری", "تولیدی", "صنعتی", "تعاونی",
)


def strip_common_company_suffixes(name: str) -> str:
    """Strips generic Persian corporate-form words (company/group/industries/trading/etc.) so
    two listings of the same entity with/without the legal-form prefix compare equal. Contains
    no real company or brand name -- these are generic Persian business-register vocabulary,
    analogous to stripping "Ltd"/"Inc"/"LLC" from a Latin company name.
    """
    normalized = normalize_persian_text(name)
    tokens = [t for t in normalized.split(" ") if t not in _COMPANY_SUFFIXES]
    return " ".join(tokens).strip()


def persian_name_variants(name: str) -> tuple[str, ...]:
    """Deterministic set of comparison variants for one Persian name: normalized, suffix-
    stripped, and a heuristic transliteration -- in that stable order, deduplicated.
    """
    normalized = normalize_persian_text(name)
    stripped = strip_common_company_suffixes(name)
    translit = transliterate_persian_heuristic(name)
    return tuple(dict.fromkeys(v for v in (normalized, stripped, translit) if v))
