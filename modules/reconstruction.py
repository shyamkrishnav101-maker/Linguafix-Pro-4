import re


class SentenceReconstructor:
    """
    Meaning reconstruction layer.

    Important: a dictionary cannot magically infer arbitrary intent.
    This module uses context and high-confidence patterns first, then
    returns multiple suggestions when the meaning is underdetermined.
    """

    def __init__(self, dictionary_engine):
        self.dictionary = dictionary_engine

    def process(self, text, intent, original):
        clean = re.sub(r"[.!?]+$", "", text.strip())
        low = clean.lower()

        # High-confidence noisy sentence reconstruction.
        patterns = [
            (
                r"^i\s+want\s+learn\s+(.+?)\s+because\s+it\s+very\s+useful\s+for\s+(.+)$",
                lambda m: f"I want to learn {m.group(1)} because it is very useful for {m.group(2)}.",
            ),
            (
                r"^i\s+need\s+(.+?)\s+for\s+college$",
                lambda m: f"I need {m.group(1)} for college.",
            ),
            (
                r"^(.+?)\s+project\s+college$",
                lambda m: f"I need a {m.group(1)} project for college.",
            ),
            (
                r"^python\s+project\s+college$",
                lambda m: "I need a Python project for college.",
            ),
            (
                r"^i\s+want\s+learn\s+python$",
                lambda m: "I want to learn Python.",
            ),
            (
                r"^i\s+want\s+python\s+course$",
                lambda m: "I want a Python course.",
            ),
            (
                r"^how\s+make\s+python\s+project$",
                lambda m: "How can I make a Python project?",
            ),
            (
                r"^she\s+going\s+college$",
                lambda m: "She is going to college.",
            ),
            (
                r"^i\s+going\s+college$",
                lambda m: "I am going to college.",
            ),
            (
                r"^they\s+going\s+college$",
                lambda m: "They are going to college.",
            ),
            (
                r"^he\s+going\s+college$",
                lambda m: "He is going to college.",
            ),
            (
                r"^python\s+project\s+need\s+(.+)$",
                lambda m: f"I need a Python project {m.group(1)}.",
            ),
        ]

        for pattern, builder in patterns:
            match = re.fullmatch(pattern, low, flags=re.I)
            if match:
                new_text = builder(match)
                return {
                    "changed": new_text.lower() != text.lower(),
                    "ambiguous": False,
                    "text": new_text,
                    "suggestions": [],
                    "message": "",
                    "issues": [{
                        "bad": text,
                        "suggestion": new_text,
                        "message": "Reconstructed the sentence from context and detected intent.",
                        "category": "Meaning reconstruction",
                        "rule_id": "SEMANTIC_RECONSTRUCTION",
                    }],
                }

        # Incomplete noun fragments: give intent-based choices rather than guessing.
        if low == "python project college":
            return self._suggest([
                "I need a Python project for college.",
                "Suggest a Python project for college.",
                "How can I build a Python project for college?",
            ])

        if low == "book it":
            return self._suggest([
                "Book a ticket.",
                "Book a hotel.",
                "Reserve a table.",
            ])

        # Subject + place fragments.
        match = re.fullmatch(
            r"(i|he|she|they|we|you)\s+(school|college|office|home)",
            low,
        )
        if match:
            subject, place = match.groups()
            subj = subject.capitalize()
            if place == "home":
                return self._suggest([
                    f"{subj} goes home.",
                    f"{subj} went home.",
                    f"{subj} is going home.",
                ])
            return self._suggest([
                f"{subj} goes to {place}.",
                f"{subj} went to {place}.",
                f"{subj} is going to {place}.",
                f"{subj} is in {place}.",
            ])

        # "want + noun" is often missing an article, but don't over-rewrite.
        match = re.fullmatch(r"i\s+want\s+(.+)", low)
        if match:
            rest = match.group(1).strip()
            if rest and " to " not in f" {rest} " and len(rest.split()) <= 5:
                return {
                    "changed": True,
                    "ambiguous": False,
                    "text": f"I want {rest}.",
                    "suggestions": [],
                    "message": "",
                    "issues": [{
                        "bad": text,
                        "suggestion": f"I want {rest}.",
                        "message": "Normalized the incomplete request without changing its meaning.",
                        "category": "Sentence reconstruction",
                        "rule_id": "SAFE_RECONSTRUCTION",
                    }],
                }

        # Leave complete sentences alone.
        return {
            "changed": False,
            "ambiguous": False,
            "text": text,
            "suggestions": [],
            "message": "",
            "issues": [],
        }

    @staticmethod
    def _suggest(suggestions):
        return {
            "changed": False,
            "ambiguous": True,
            "text": "",
            "suggestions": suggestions,
            "message": "This input has multiple plausible meanings. Choose the sentence closest to your intention.",
            "issues": [],
        }
