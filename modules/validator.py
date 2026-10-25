import re


def validate_sentence(original, corrected, intent, dictionary_engine):
    """
    Lightweight final validation.
    Returns a conservative confidence estimate and suggestions.
    """
    suggestions = []

    if not corrected.strip():
        return {"confidence": 0.0, "suggestions": []}

    words = re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", corrected)

    if not words:
        return {"confidence": 0.2, "suggestions": []}

    known = 0
    for word in words:
        if dictionary_engine.is_known(word):
            known += 1

    dictionary_ratio = known / len(words)

    confidence = 0.55 + (dictionary_ratio * 0.35)

    # A very short fragment is inherently less certain.
    if len(words) < 3:
        confidence -= 0.15

    # If the original is substantially different, confidence is reduced.
    original_words = len(re.findall(r"\b[A-Za-z][A-Za-z'-]*\b", original))
    if original_words and len(words) > original_words + 5:
        confidence -= 0.10

    confidence = max(0.0, min(1.0, confidence))

    return {
        "confidence": round(confidence, 2),
        "suggestions": suggestions,
    }
