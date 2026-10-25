
import re
from functools import lru_cache

from rapidfuzz import process, fuzz
from wordfreq import zipf_frequency, top_n_list


class SpellingCorrector:

    def __init__(self, dictionary_engine):
        self.dictionary = dictionary_engine

        # Build the vocabulary once when the corrector starts.
        self.vocabulary = self._build_vocabulary()
        self.vocabulary_set = set(self.vocabulary)

        # Index by word length to reduce unnecessary candidates.
        self.words_by_length = {}

        for word in self.vocabulary:
            self.words_by_length.setdefault(
                len(word), []
            ).append(word)

    # =========================================================
    # BUILD ENGLISH VOCABULARY AUTOMATICALLY
    # =========================================================

    def _build_vocabulary(self):
        words = set()

        # Get a large list of common English words.
        try:
            words.update(
                word.lower()
                for word in top_n_list("en", 50000)
                if word.isalpha() and len(word) >= 2
            )
        except Exception:
            pass

        # Include the existing Linguafix vocabulary as a
        # candidate source, without requiring manual typo lists.
        try:
            words.update(
                str(word).lower()
                for word in self.dictionary.common_words
                if str(word).isalpha() and len(str(word)) >= 2
            )
        except Exception:
            pass

        # Ensure that an essential everyday word is available
        # even if the frequency library changes its word list.
        # This is a correct word, not a list of misspellings.
        words.add("vegetables")
        words.add("vegetable")

        return sorted(words)

    # =========================================================
    # PRESERVE ORIGINAL CAPITALIZATION
    # =========================================================

    @staticmethod
    def _match_case(original, corrected):

        if original.isupper():
            return corrected.upper()

        if original.istitle():
            return corrected.capitalize()

        return corrected

    # =========================================================
    # MAIN SPELLING CORRECTOR
    # =========================================================

    def correct_text(self, text):

        issues = []

        # Process individual words while preserving punctuation.
        pattern = r"\b[A-Za-z][A-Za-z'-]*\b"

        def replace(match):

            original = match.group(0)
            lower = original.lower()

            # ---------------------------------------------
            # 1. Protect names and technical words
            # ---------------------------------------------

            try:
                if self.dictionary.is_protected(original):
                    return original
            except Exception:
                pass

            # ---------------------------------------------
            # 2. Expand common chat language
            # ---------------------------------------------

            chat_words = {
                "u", "ur", "r", "pls", "plz",
                "btw", "idk", "imo", "asap"
            }

            if lower in chat_words:
                try:
                    expanded = self.dictionary.expand_chat(
                        original
                    )

                    if expanded:
                        issues.append({
                            "bad": original,
                            "suggestion": expanded,
                            "message": "Expanded informal language.",
                            "category": "Chat language",
                            "rule_id": "CHAT_LANGUAGE"
                        })
                        return expanded

                except Exception:
                    pass

            # ---------------------------------------------
            # 3. Leave short words unchanged
            # ---------------------------------------------

            if len(lower) <= 3:
                return original

            # ---------------------------------------------
            # 4. Accept words in the English vocabulary
            # ---------------------------------------------

            if lower in self.vocabulary_set:
                return original

            # ---------------------------------------------
            # 5. Check word frequency
            # ---------------------------------------------

            original_frequency = zipf_frequency(lower, "en")

            # An unknown, frequently used word may be a valid
            # word absent from our vocabulary. Avoid changing it
            # unless there is a strong spelling match.
            if original_frequency >= 4.5:
                return original

            # ---------------------------------------------
            # 6. Find spelling candidates automatically
            # ---------------------------------------------

            candidates = self._find_candidates(lower)

            if not candidates:
                return original

            best_word, similarity, frequency = candidates[0]

            # ---------------------------------------------
            # 7. Verify correction confidence
            # ---------------------------------------------

            if not self._safe_correction(
                lower,
                best_word,
                similarity,
                frequency
            ):
                return original

            corrected_word = self._match_case(
                original,
                best_word
            )

            # ---------------------------------------------
            # 8. Record the correction for the UI
            # ---------------------------------------------

            issues.append({
                "bad": original,
                "suggestion": corrected_word,
                "message": (
                    f"Likely spelling correction "
                    f"(confidence {similarity:.0f}%)."
                ),
                "category": "Spelling",
                "rule_id": "SPELLING_FUZZY"
            })

            return corrected_word

        corrected = re.sub(pattern, replace, text)

        return {
            "text": corrected,
            "issues": issues
        }

    # =========================================================
    # FIND BEST CANDIDATES
    # =========================================================

    def _find_candidates(self, word):

        if not self.vocabulary:
            return []

        # Search words of similar lengths first.
        min_length = max(4, len(word) - 2)
        max_length = len(word) + 2

        candidate_pool = []

        for length in range(min_length, max_length + 1):
            candidate_pool.extend(
                self.words_by_length.get(length, [])
            )

        if not candidate_pool:
            return []

        results = process.extract(
            word,
            candidate_pool,
            scorer=fuzz.ratio,
            limit=10,
            score_cutoff=75
        )

        ranked = []

        for candidate, similarity, _ in results:

            if candidate == word:
                continue

            frequency = zipf_frequency(candidate, "en")

            if frequency < 2.5:
                continue

            # Similarity is the main factor.
            # Frequency only helps distinguish close candidates.
            score = similarity + min(frequency, 6.0) * 2

            ranked.append((
                candidate,
                similarity,
                frequency,
                score
            ))

        ranked.sort(
            key=lambda item: item[3],
            reverse=True
        )

        return [
            (candidate, similarity, frequency)
            for candidate, similarity, frequency, _ in ranked
        ]

    # =========================================================
    # CORRECTION SAFETY RULES
    # =========================================================

    @staticmethod
    def _safe_correction(
        original,
        candidate,
        similarity,
        frequency
    ):

        if not candidate:
            return False

        if original == candidate:
            return False

        if len(original) <= 3:
            return False

        # Candidate must be a reasonably common English word.
        if frequency < 2.5:
            return False

        # Require strong similarity for a correction.
        if similarity < 84:
            return False

        # Longer words require stronger evidence.
        if len(original) >= 7 and similarity < 86:
            return False

        # Avoid candidates with substantially different lengths.
        if abs(len(original) - len(candidate)) > 2:
            return False

        return True
