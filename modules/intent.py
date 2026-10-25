import re


class IntentDetector:
    def detect(self, text):
        t = text.lower().strip()

        if re.match(r"^(hi|hello|hey)\b", t):
            return "greeting"

        if any(x in t for x in ["translate", "translation"]):
            return "translation"

        if any(x in t for x in ["summarize", "summary", "shorten this"]):
            return "summarization"

        if any(x in t for x in ["correct this", "fix my grammar", "grammar", "correct sentence"]):
            return "correction"

        if any(x in t for x in ["suggest", "recommend", "which", "best"]):
            return "recommendation"

        if any(x in t for x in ["how to", "how do i", "how can i", "what is", "why is", "why does"]):
            return "question"

        if "?" in t:
            return "question"

        if any(x in t for x in [
            "python", "java", "javascript", "code", "coding", "program",
            "programming", "project", "flask", "react", "api"
        ]):
            return "programming"

        if any(x in t for x in ["explain", "meaning", "what does"]):
            return "explanation"

        if any(x in t for x in ["please", "need", "want", "help me", "give me"]):
            return "request"

        return "general"
