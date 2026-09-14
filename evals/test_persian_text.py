from __future__ import annotations

import unittest

from persian_text import (
    normalize_persian_text,
    persian_name_variants,
    strip_common_company_suffixes,
    transliterate_persian_heuristic,
)


class NormalizationTests(unittest.TestCase):
    def test_arabic_yeh_normalizes_to_persian_yeh(self):
        self.assertEqual(normalize_persian_text("علي"), normalize_persian_text("علی"))

    def test_arabic_kaf_normalizes_to_persian_kaf(self):
        self.assertIn("ک", normalize_persian_text("پاك"))

    def test_half_space_normalizes_to_regular_space(self):
        with_half_space = "می‌شود"
        without = normalize_persian_text(with_half_space)
        self.assertNotIn("‌", without)

    def test_arabic_indic_digits_normalize_to_latin(self):
        self.assertEqual(normalize_persian_text("١٢٣"), "123")

    def test_persian_digits_normalize_to_latin(self):
        self.assertEqual(normalize_persian_text("۱۲۳"), "123")

    def test_alef_variants_normalize_to_bare_alef(self):
        self.assertEqual(normalize_persian_text("آب"), normalize_persian_text("اب"))
        self.assertEqual(normalize_persian_text("آ"), "ا")

    def test_diacritics_are_stripped(self):
        self.assertNotIn("ً", normalize_persian_text("مَحل"))

    def test_extra_whitespace_is_collapsed(self):
        self.assertEqual(normalize_persian_text("شرکت   نمونه"), "شرکت نمونه")

    def test_empty_string_returns_empty(self):
        self.assertEqual(normalize_persian_text(""), "")

    def test_normalization_is_idempotent(self):
        text = "شركت  ‌نمونة"
        once = normalize_persian_text(text)
        twice = normalize_persian_text(once)
        self.assertEqual(once, twice)

    def test_two_differently_typed_spellings_of_the_same_word_converge(self):
        variant_a = "بازرگاني"  # Arabic yeh
        variant_b = "بازرگانی"  # Persian yeh
        self.assertEqual(normalize_persian_text(variant_a), normalize_persian_text(variant_b))


class TransliterationTests(unittest.TestCase):
    def test_transliteration_is_deterministic(self):
        self.assertEqual(transliterate_persian_heuristic("شرکت نمونه"), transliterate_persian_heuristic("شرکت نمونه"))

    def test_transliteration_produces_latin_characters(self):
        result = transliterate_persian_heuristic("شرکت")
        self.assertTrue(all(ord(c) < 128 for c in result))

    def test_transliteration_never_raises_on_mixed_script_input(self):
        transliterate_persian_heuristic("ABC شرکت 123")  # must not raise


class CompanySuffixStrippingTests(unittest.TestCase):
    def test_generic_suffix_is_stripped(self):
        # "شرکت نمونه" ("Example Company") -- a generic placeholder, not a real company name
        stripped = strip_common_company_suffixes("شرکت نمونه")
        self.assertNotIn("شرکت", stripped.split(" "))
        self.assertIn("نمونه", stripped)

    def test_name_without_suffix_is_unchanged_besides_normalization(self):
        self.assertEqual(strip_common_company_suffixes("نمونه"), "نمونه")

    def test_multiple_suffixes_are_all_stripped(self):
        stripped = strip_common_company_suffixes("گروه صنایع نمونه")
        for suffix in ("گروه", "صنایع"):
            self.assertNotIn(suffix, stripped.split(" "))


class NameVariantsTests(unittest.TestCase):
    def test_variants_are_deterministic_and_deduplicated(self):
        first = persian_name_variants("شرکت نمونه")
        second = persian_name_variants("شرکت نمونه")
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(set(first)))

    def test_variants_include_normalized_and_stripped_forms(self):
        variants = persian_name_variants("شرکت نمونه")
        self.assertIn("نمونه", variants)  # suffix-stripped form

    def test_two_spelling_variants_of_the_same_name_share_a_common_variant(self):
        variants_a = set(persian_name_variants("شركت نمونة"))
        variants_b = set(persian_name_variants("شرکت نمونه"))
        self.assertTrue(variants_a & variants_b)


if __name__ == "__main__":
    unittest.main()
