from flask import Flask, render_template, request, jsonify

import re

import os

import json

import requests

from dotenv import load_dotenv

from modules.dictionary import DictionaryEngine

from modules.spelling import SpellingCorrector

from modules.intent import IntentDetector

from modules.reconstruction import SentenceReconstructor

from modules.validator import validate_sentence

# ============================================================

# ENVIRONMENT

# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SEMANTIC_MODEL = {"model": "openai/gpt-oss-120b"}

# ============================================================

# FLASK APP

# ============================================================

app = Flask(__name__)

# ============================================================

# EXISTING LINGUAFIX ENGINES

# ============================================================

dictionary_engine = DictionaryEngine()

spelling_engine = SpellingCorrector(

    dictionary_engine

)

intent_engine = IntentDetector()

reconstructor = SentenceReconstructor(

    dictionary_engine

)

# ============================================================

# NORMALIZATION

# ============================================================

def normalize(text):

    text = (

        text or ""

    ).replace(

        "\r\n",

        "\n"

    ).replace(

        "\r",

        "\n"

    )

    lines = [

        re.sub(

            r"[ \t]+",

            " ",

            line

        ).strip()

        for line in text.split("\n")

    ]

    return "\n".join(lines).strip()

# ============================================================

# SPACING

# ============================================================

def fix_spacing(text):

    text = re.sub(

        r"[ \t]+([,.!?;:])",

        r"\1",

        text

    )

    text = re.sub(

        r"([,.!?;:])([A-Za-z])",

        r"\1 \2",

        text

    )

    return text

# ============================================================

# CAPITALIZATION

# ============================================================

def capitalize_sentences(text):

    return re.sub(

        r"(^|[.!?]\s+)([a-z])",

        lambda m:

            m.group(1)

            + m.group(2).upper(),

        text

    )

# ============================================================

# SENTENCE COUNT

# ============================================================

def sentence_count(text):

    return len([

        s

        for s in re.split(

            r"(?<=[.!?])\s+",

            text.strip()

        )

        if s.strip()

    ])

# ============================================================

# STATISTICS

# ============================================================

def stats(text, issues):

    words = re.findall(

        r"\b[\w'-]+\b",

        text,

        flags=re.UNICODE

    )

    density = (

        len(issues)

        /

        max(len(words), 1)

    )

    score = max(

        0,

        min(

            100,

            round(

                100 - density * 25

            )

        )

    )

    return {

        "words":

            len(words),

        "sentences":

            sentence_count(text),

        "characters":

            len(text),

        "unique_words":

            len(

                set(

                    w.lower()

                    for w in words

                )

            ),

        "issues":

            len(issues),

        "score":

            score,

    }

# ============================================================

# CAPITALIZATION ISSUES

# ============================================================

# ============================================================

# CAPITALIZATION ISSUES

# ============================================================

def capitalization_issues(raw):

    issues = []

    for m in re.finditer(

        r"(^|[.!?]\s+)([a-z])",

        raw

    ):

        issues.append({

            "bad": m.group(2),

            "suggestion": m.group(2).upper(),

            "correction": m.group(2).upper(),

            "type": "Capitalization",

            "message":

                "Capitalize the first letter of a sentence.",

            "category": "Capitalization",

            "rule_id": "CAPITALIZE_SENTENCE",

        })

    return issues

# ============================================================

# BASIC GRAMMAR

# ============================================================

def apply_basic_grammar(text):

    """

    Conservative local grammar and spelling rules.

    These rules are NOT responsible for understanding

    the user's intended meaning.

    Semantic reconstruction happens separately.

    """

    rules = [

        (

            r"\b(I)\s+(has)\b",

            r"\1 have",

            "Use 'have' with 'I'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(have)\b",

            r"\1 has",

            "A singular subject uses 'has'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(go)\s+(to)\b",

            r"\1 goes \3",

            "Use the third-person singular form 'goes'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(do)\b",

            r"\1 does",

            "A singular subject uses 'does'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(like)\b",

            r"\1 likes",

            "A singular subject uses 'likes'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(play)\b",

            r"\1 plays",

            "A singular subject uses 'plays'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(work)\b",

            r"\1 works",

            "A singular subject uses 'works'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(need)\b",

            r"\1 needs",

            "A singular subject uses 'needs'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+(want)\b",

            r"\1 wants",

            "A singular subject uses 'wants'.",

            "Grammar"

        ),

        (

            r"\b(they|we|you)\s+(goes)\b",

            r"\1 go",

            "Use the base verb with 'they', 'we', or 'you'.",

            "Grammar"

        ),

        (

            r"\b(they|we|you)\s+(has)\b",

            r"\1 have",

            "Use 'have' with 'they', 'we', or 'you'.",

            "Grammar"

        ),

        (

            r"\b(they|we|you)\s+(is)\b",

            r"\1 are",

            "Use 'are' with 'they', 'we', or 'you'.",

            "Grammar"

        ),

        (

            r"\b(they|we|you)\s+(was)\b",

            r"\1 were",

            "Use 'were' with 'they', 'we', or 'you'.",

            "Grammar"

        ),

        (

            r"\b(I)\s+(is|are)\b",

            r"\1 am",

            "Use 'am' with 'I'.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+don't\b",

            r"\1 doesn't",

            "Use 'doesn't' with a singular subject.",

            "Grammar"

        ),

        (

            r"\b(he|she|it)\s+do\s+not\b",

            r"\1 does not",

            "Use 'does not' with a singular subject.",

            "Grammar"

        ),

        (

            r"\b(I)\s+(going|coming|working|studying|eating|playing|reading|writing|learning)\b",

            r"\1 am \2",

            "A progressive verb needs 'am' with 'I'.",

            "Missing word"

        ),

        (

            r"\b(he|she|it)\s+(going|coming|working|studying|eating|playing|reading|writing|learning)\b",

            r"\1 is \2",

            "A progressive verb needs 'is'.",

            "Missing word"

        ),

        (

            r"\b(they|we|you)\s+(going|coming|working|studying|eating|playing|reading|writing|learning)\b",

            r"\1 are \2",

            "A progressive verb needs 'are'.",

            "Missing word"

        ),

        (

            r"\b(a)\s+(apple|orange|elephant|engineer|artist|hour|honest)\b",

            lambda m:

                f"an {m.group(2)}",

            "Use 'an' before a vowel sound.",

            "Grammar"

        ),

        (

            r"\b(an)\s+(book|car|dog|student|university|European)\b",

            lambda m:

                f"a {m.group(2)}",

            "Use 'a' before a consonant sound.",

            "Grammar"

        ),

        (

            r"\bgrammer\b",

            "grammar",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\brecieve\b",

            "receive",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\bteh\b",

            "the",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\bdefinately\b",

            "definitely",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\bseperate\b",

            "separate",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\boccured\b",

            "occurred",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\bwich\b",

            "which",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\buntill\b",

            "until",

            "Possible spelling mistake.",

            "Spelling"

        ),

        (

            r"\beveryday\b",

            "every day",

            "Use 'every day' when you mean 'each day'.",

            "Usage"

        ),

        (

            r"\binformations\b",

            "information",

            "Use the uncountable noun 'information'.",

            "Usage"

        ),

        (

            r"\badvices\b",

            "advice",

            "Use the uncountable noun 'advice'.",

            "Usage"

        ),

        (

            r"\bdiscuss about\b",

            "discuss",

            "Use 'discuss' without 'about'.",

            "Usage"

        ),

        (

            r"\breturn back\b",

            "return",

            "The word 'back' is usually unnecessary after 'return'.",

            "Usage"

        ),

    ]

    current = text

    issues = []

    for _ in range(3):

        changed = False

        for (

            pattern,

            replacement,

            message,

            category

        ) in rules:

            def repl(m):

                nonlocal changed

                old = m.group(0)

                new = (

                    replacement(m)

                    if callable(replacement)

                    else m.expand(replacement)

                )

                if new == old:

                    return old

                changed = True

                issues.append({

                    "bad":

                        old,

                    "suggestion":

                        new,

                    "message":

                        message,

                    "category":

                        category,

                    "rule_id":

                        "LOCAL_RULE",

                })

                return new

            current = re.sub(

                pattern,

                repl,

                current,

                flags=re.I

            )

        if not changed:

            break

    return current, issues

# ============================================================

# END PUNCTUATION

# ============================================================

def end_punctuation(text):

    text = text.rstrip()

    if not text:

        return text, None

    if text[-1] not in ".!?":

        if len(

            re.findall(

                r"\b[\w'-]+\b",

                text

            )

        ) >= 3:

            return text + ".", {

                "bad":

                    "",

                "suggestion":

                    ".",

                "message":

                    "Add end punctuation to complete the sentence.",

                "category":

                    "Punctuation",

                "rule_id":

                    "END_PUNCTUATION",

            }

    return text, None

# ============================================================

# DETERMINISTIC AMBIGUITY GUARD

# ============================================================

# ============================================================

# SUGGESTION TEXT NORMALIZATION

# ============================================================

def normalize_suggestion_text(text):

    """

    Clean and normalize generated meaning suggestions.

    Examples:

        want learn python

        ->

        I want to learn Python.

        need learn javascript

        ->

        I need to learn JavaScript.

    """

    text = re.sub(

        r"\s+",

        " ",

        (text or "").strip()

    )

    if not text:

        return text

    # Capitalize first character.

    text = text[0].upper() + text[1:]

    # Technical / programming names.

    replacements = {

        r"\bpython\b": "Python",

        r"\bjavascript\b": "JavaScript",

        r"\btypescript\b": "TypeScript",

        r"\bhtml\b": "HTML",

        r"\bcss\b": "CSS",

        r"\bflask\b": "Flask",

        r"\bmongodb\b": "MongoDB",

        r"\breact\b": "React",

        r"\bnodejs\b": "Node.js",

        r"\bnode\.js\b": "Node.js",

        r"\bgithub\b": "GitHub",

        r"\bapi\b": "API",

        r"\bapis\b": "APIs",

        r"\bai\b": "AI",

        r"\bml\b": "ML",

    }

    for pattern, replacement in replacements.items():

        text = re.sub(

            pattern,

            replacement,

            text,

            flags=re.IGNORECASE

        )

    # Add punctuation if missing.

    if text[-1] not in ".!?":

        text += "."

    return text

# ============================================================

# DETERMINISTIC AMBIGUITY GUARD

# ============================================================

def build_tense_ambiguity_suggestions(text):

    """

    Generate multiple possible meanings for short,

    incomplete or tense-ambiguous sentences.

    Examples:

        i buy laptop

    becomes:

        I will buy laptop.

        I am buying laptop.

        I buy laptop.

    And:

        want learn python

    becomes:

        I want to learn Python.

    The function is deliberately conservative.

    It must NOT treat words such as "want" or "need"

    as grammatical subjects.

    """

    clean = re.sub(

        r"\s+",

        " ",

        (text or "").strip()

    )

    if not clean:

        return None

    # --------------------------------------------------------

    # EXPLICIT TIME / TENSE MARKERS

    # --------------------------------------------------------

    explicit_markers = {

        "yesterday",

        "today",

        "tomorrow",

        "tonight",

        "last",

        "ago",

        "earlier",

        "previously",

        "already",

        "now",

        "currently",

        "right now",

        "at the moment",

        "next",

        "soon",

        "later",

        "will",

        "would",

        "can",

        "could",

        "should",

        "must",

        "shall",

        "going to",

        "plan to",

        "want to",

        "need to"

    }

    lower = clean.lower()

    if any(

        marker in lower

        for marker in explicit_markers

    ):

        return None

    # Remove final punctuation before analysis.

    parts = (

        clean

        .rstrip(".!?")

        .split()

    )

    if len(parts) < 3:

        return None

    # ========================================================

    # SPECIAL CASE:

    # "want learn python"

    # "want buy laptop"

    # "need learn java"

    # ========================================================

    first_word = parts[0].lower()

    if first_word in {

        "want",

        "need"

    } and len(parts) >= 3:

        action = parts[1].lower()

        object_text = " ".join(

            parts[2:]

        ).strip(" .!?")

        if not action or not object_text:

            return None

        if first_word == "want":

            suggestion = (

                f"I want to "

                f"{action} "

                f"{object_text}."

            )

            reason = (

                "The input appears to express "

                "a personal desire or intention."

            )

        else:

            suggestion = (

                f"I need to "

                f"{action} "

                f"{object_text}."

            )

            reason = (

                "The input appears to express "

                "a personal need."

            )

        suggestion = normalize_suggestion_text(

            suggestion

        )

        return {

            "base": suggestion,

            "suggestions": [

                {

                    "text": suggestion,

                    "reason": reason,

                    "confidence": 0.92

                }

            ]

        }

    # ========================================================

    # NORMAL SUBJECT + VERB + OBJECT

    # ========================================================

    subject = parts[0].lower()

    verb = parts[1].lower()

    rest = " ".join(

        parts[2:]

    ).strip(" .!?")

    if not rest:

        return None

    # --------------------------------------------------------

    # STATIVE VERBS

    # --------------------------------------------------------

    clear_stative_verbs = {

        "like",

        "love",

        "hate",

        "know",

        "understand",

        "want",

        "need",

        "prefer",

        "believe",

        "think",

        "remember",

        "own",

        "have",

        "feel",

        "seem",

        "mean",

        "agree",

        "disagree"

    }

    if verb in clear_stative_verbs:

        return None

    # --------------------------------------------------------

    # ALREADY INFLECTED / AUXILIARY VERBS

    # --------------------------------------------------------

    if (

        verb.endswith("ed")

        or verb.endswith("ing")

        or verb in {

            "am",

            "is",

            "are",

            "was",

            "were",

            "has",

            "have",

            "had",

            "do",

            "does",

            "did",

            "will",

            "would",

            "can",

            "could",

            "should",

            "may",

            "might",

            "must",

            "shall"

        }

    ):

        return None

    # ========================================================

    # ONLY ACCEPT REAL SUBJECT PRONOUNS

    # ========================================================

    valid_subjects = {

        "i",

        "we",

        "you",

        "they",

        "he",

        "she"

    }

    if subject not in valid_subjects:

        return None

    # ========================================================

    # COMMON ACTION VERBS

    # ========================================================

    common_verbs = {

        "buy",

        "meet",

        "go",

        "come",

        "visit",

        "call",

        "see",

        "eat",

        "drink",

        "play",

        "watch",

        "read",

        "write",

        "study",

        "work",

        "travel",

        "start",

        "finish",

        "join",

        "send",

        "take",

        "make",

        "get",

        "give",

        "bring",

        "use",

        "open",

        "close",

        "learn",

        "teach",

        "help",

        "ask",

        "tell",

        "message",

        "talk",

        "speak",

        "attend",

        "submit",

        "apply",

        "choose",

        "select",

        "practice",

        "practice",

        "develop",

        "build",

        "create",

        "install",

        "run",

        "test",

        "check",

        "fix",

        "complete"

    }

    if verb not in common_verbs:

        return None

    # ========================================================

    # GENERATE MEANING OPTIONS

    # ========================================================

    if subject == "i":

        base = (

            f"I {verb} "

            f"{rest}."

        )

        options = [

            {

                "text": (

                    f"I will "

                    f"{verb} "

                    f"{rest}."

                ),

                "reason": (

                    "The input may describe "

                    "a future intention or planned action."

                ),

                "confidence": 0.78

            },

            {

                "text": (

                    f"I am "

                    f"{verb}ing "

                    f"{rest}."

                ),

                "reason": (

                    "The input may describe "

                    "an action happening now or around now."

                ),

                "confidence": 0.68

            },

            {

                "text": base,

                "reason": (

                    "The input may describe "

                    "a present or habitual action."

                ),

                "confidence": 0.62

            }

        ]

    elif subject in {

        "he",

        "she"

    }:

        base = (

            f"{subject} "

            f"{verb}s "

            f"{rest}."

        )

        options = [

            {

                "text": (

                    f"{subject} will "

                    f"{verb} "

                    f"{rest}."

                ),

                "reason": (

                    "The input may describe "

                    "a future action."

                ),

                "confidence": 0.76

            },

            {

                "text": (

                    f"{subject} is "

                    f"{verb}ing "

                    f"{rest}."

                ),

                "reason": (

                    "The input may describe "

                    "an ongoing action."

                ),

                "confidence": 0.67

            },

            {

                "text": base,

                "reason": (

                    "The input may describe "

                    "a present or habitual action."

                ),

                "confidence": 0.61

            }

        ]

    else:

        base = (

            f"{subject} "

            f"{verb} "

            f"{rest}."

        )

        options = [

            {

                "text": (

                    f"{subject} will "

                    f"{verb} "

                    f"{rest}."

                ),

                "reason": (

                    "The input may describe "

                    "a future action."

                ),

                "confidence": 0.76

            },

            {

                "text": (

                    f"{subject} are "

                    f"{verb}ing "

                    f"{rest}."

                ),

                "reason": (

                    "The input may describe "

                    "an ongoing action."

                ),

                "confidence": 0.67

            },

            {

                "text": base,

                "reason": (

                    "The input may describe "

                    "a present or habitual action."

                ),

                "confidence": 0.61

            }

        ]

    # ========================================================

    # NORMALIZE ALL SUGGESTIONS

    # ========================================================

    for option in options:

        option["text"] = (

            normalize_suggestion_text(

                option["text"]

            )

        )

    base = normalize_suggestion_text(

        base

    )

    # ========================================================

    # REMOVE DUPLICATES

    # ========================================================

    seen = set()

    result = []

    for option in options:

        key = (

            option["text"]

            .strip()

            .lower()

        )

        if key not in seen:

            seen.add(key)

            result.append(

                option

            )

    # Maximum three suggestions.

    result = result[:3]

    return {

        "base": base,

        "suggestions": result

    }

# ============================================================

# AI SEMANTIC RECONSTRUCTION

# ============================================================

def semantic_reconstruct(text):

    """

    Understand the meaning of the user's sentence.

    This is different from grammar correction.

    Example:

        sushanth good by

    Possible meanings:

        Sushanth is a good boy.

        Goodbye, Sushanth.

    The AI must choose the strongest interpretation

    when confidence is high and provide alternatives

    when the meaning is genuinely uncertain.

    """

    if not GROQ_API_KEY:

        print(

            "WARNING: GROQ_API_KEY is not configured."

        )

        return {

            "available":

                False,

            "corrected":

                text,

            "intent":

                "unknown",

            "confidence":

                0,

            "ambiguous":

                False,

            "suggestions":

                []

        }

    system_prompt = """

You are the semantic reconstruction engine for LinguaFix Pro.

Your primary job is to understand the USER'S INTENDED MEANING.

You are NOT merely a spelling, grammar, capitalization, or

punctuation corrector.

The user may write incomplete, broken, abbreviated, informal,

speech-to-text-like, or conversational English. Reconstruct the

sentence only when the intended meaning is sufficiently supported

by the input.

============================================================

CORE PRINCIPLE

============================================================

Always separate these two questions:

1. Can I make this text grammatically correct?

2. Do I actually know what the user intended?

A grammatically valid sentence is NOT automatically the correct

interpretation of the user's meaning.

Never silently choose a tense, event, relationship, location,

emotion, or intention that is not supported by the input.

============================================================

CLEAR INTENT

============================================================

If the intended meaning is strongly supported by the input:

- Return ONE natural corrected sentence.

- Preserve the original meaning.

- Repair missing auxiliary verbs, articles, prepositions,

  pronouns, word order, spelling, and punctuation when justified.

- Add missing words only when the meaning strongly supports them.

- Do not create unnecessary suggestions.

- Set "ambiguous" to false.

- Use a high confidence only when the user's meaning is genuinely

  clear.

Examples:

Input:

i going college

Corrected:

I am going to college.

Input:

he very good player

Corrected:

He is a very good player.

Input:

you coming or not

Corrected:

Are you coming or not?

Input:

i not understand what saying

Corrected:

I don't understand what you are saying.

Input:

tomorrow exam me

Corrected:

I have an exam tomorrow.

Input:

yesterday i buy laptop

Corrected:

Yesterday, I bought a laptop.

The word "yesterday" provides strong evidence for past tense.

Input:

tomorrow i buy laptop

Corrected:

Tomorrow, I will buy a laptop.

The word "tomorrow" provides strong evidence for future meaning.

============================================================

GENUINELY AMBIGUOUS INTENT

============================================================

If TWO OR MORE materially different meanings are reasonably

possible, DO NOT arbitrarily choose one as the user's meaning.

Set:

"ambiguous": true

Use a lower confidence value.

Return realistic alternatives in "suggestions".

The "corrected" field must NOT pretend that one interpretation

is certain. It may contain the safest minimally corrected form

of the original text, but it must not silently convert an

ambiguous tense into past, present continuous, or future.

IMPORTANT EXAMPLE:

Input:

i buy laptop

This is ambiguous.

It could mean:

I will buy a laptop.

I am buying a laptop.

I bought a laptop.

I buy laptops.

There is not enough information in the input to know which tense

or aspect the user intended.

Therefore DO NOT return only:

I bought a laptop.

Instead return:

"ambiguous": true

and provide realistic suggestions.

============================================================

TENSE SAFETY

============================================================

Never infer tense merely because one tense produces a grammatical

sentence.

For example:

"i buy laptop"

does NOT prove:

"I bought a laptop."

It may describe:

- future intention

- current action

- past action

- habitual action

Look for evidence such as:

Past:

yesterday, last week, last night, ago, previously, earlier,

already, did, was, were, etc.

Future:

tomorrow, next week, later, soon, will, going to, plan to,

etc.

Current/ongoing:

now, right now, currently, at the moment, am/is/are + verb-ing,

etc.

If there is no sufficient evidence and multiple interpretations

remain realistic, mark the result ambiguous.

Do NOT treat every simple present sentence as ambiguous.

For example:

"I like pizza."

has a clear habitual/state meaning and does not require

unnecessary suggestions.

============================================================

DO NOT INVENT INFORMATION

============================================================

Never invent:

- tense

- time

- location

- relationship

- event

- person

- object

- intention

- emotion

- ownership

- action

unless the input provides enough evidence.

Example:

Input:

rahul good

Do NOT automatically create:

Rahul is a good boy.

The word "boy" was not provided.

A safer interpretation may be:

Rahul is good.

If the missing information changes the meaning materially,

provide suggestions instead of inventing facts.

============================================================

SEMANTIC RECONSTRUCTION RULES

============================================================

1. Understand the complete input before correcting it.

2. Correct grammar naturally.

3. Preserve names.

4. Preserve important nouns and technical terms.

5. Preserve the user's actual meaning.

6. Reorder words when necessary.

7. Add missing grammar when strongly supported.

8. Understand conversational Indian English.

9. Understand short messages.

10. Understand missing auxiliary verbs.

11. Understand missing articles.

12. Understand missing pronouns.

13. Understand reversed or incomplete subject/verb structures.

14. Do not change meaning merely to make grammar perfect.

15. Prefer natural everyday English.

16. Do not simply capitalize the first letter.

17. Do not simply add punctuation.

18. Do not blindly correct individual words.

============================================================

SUGGESTIONS

============================================================

Suggestions are required when the user's intended meaning is

genuinely uncertain.

Suggestions must represent DIFFERENT POSSIBLE MEANINGS, not

minor grammar or punctuation variations.

Good:

Input:

i buy laptop

Suggestions:

I will buy a laptop.

I am buying a laptop.

I bought a laptop.

I buy laptops.

Bad:

I buy a laptop.

I buy a laptop!

I buy a laptop.

Do not return duplicates.

Each suggestion must contain:

- text

- reason

- confidence

Only include realistic interpretations supported by the input.

Usually return 2 to 4 suggestions when ambiguity is real.

Do not create alternatives merely to make the response longer.

============================================================

SPECIAL AMBIGUITY EXAMPLES

============================================================

Input:

sushanth good by

This can have multiple interpretations.

Possible meanings include:

Sushanth is a good boy.

Goodbye, Sushanth.

Because the input does not provide enough context, mark it

ambiguous and provide both realistic interpretations.

Input:

i meet rahul

Possible interpretations can include:

I will meet Rahul.

I am meeting Rahul.

I met Rahul.

I meet Rahul regularly.

Do not select one tense without evidence.

Input:

i am meeting rahul tomorrow

Corrected:

I am meeting Rahul tomorrow.

The tense and time are already clear.

============================================================

CONFIDENCE

============================================================

Confidence must be a number between 0 and 1.

Confidence means confidence in the USER'S INTENDED MEANING,

not confidence that a grammatical sentence can be generated.

Use approximately:

0.85 to 1.00:

Meaning is strongly supported.

0.60 to 0.84:

Meaning is reasonably supported but some information is missing.

Below 0.60:

Multiple realistic interpretations remain.

When multiple meanings are realistic, "ambiguous" MUST be true.

Never use 0.99 simply because the resulting sentence is

grammatically correct.

============================================================

OUTPUT

============================================================

Return ONLY valid JSON.

Use exactly this structure:

{

    "corrected": "best safe corrected sentence",

    "intent": "short description of the user's likely meaning",

    "confidence": 0.0,

    "ambiguous": false,

    "suggestions": [

        {

            "text": "alternative sentence",

            "reason": "why this may be what the user meant",

            "confidence": 0.0

        }

    ]

}

When the meaning is clear:

"ambiguous": false

"suggestions": []

When the meaning is genuinely ambiguous:

"ambiguous": true

"suggestions": [realistic alternatives]

============================================================

FINAL SAFETY CHECK BEFORE ANSWERING

============================================================

Before returning JSON, ask yourself:

1. Did I choose a tense that the input does not support?

2. Did I invent a fact that was not provided?

3. Are there two or more materially different meanings?

4. If yes, did I set "ambiguous" to true?

5. Are my suggestions genuinely different meanings?

6. Did I avoid unnecessary alternatives?

7. Is the corrected sentence faithful to the user's words?

If the answer to question 3 is YES, do NOT force one

interpretation as certain.

Return JSON only. Do not return markdown.

"""

    user_prompt = f"""

Analyze the following user input.

USER INPUT:

{text}

Understand the intended meaning.

Do not merely fix punctuation.

Do not merely fix capitalization.

Return the best natural English reconstruction.

If the meaning is uncertain, provide realistic alternatives.

Return JSON only.

"""

    try:

        response = requests.post(

    GROQ_URL,

    headers={

        "Authorization": f"Bearer {GROQ_API_KEY}",

        "Content-Type": "application/json"

    },

    json={

        "model": SEMANTIC_MODEL["model"],

        "temperature": 0.1,

        "response_format": {

            "type": "json_object"

        },

                "messages": [

                    {

                        "role":

                            "system",

                        "content":

                            system_prompt

                    },

                    {

                        "role":

                            "user",

                        "content":

                            user_prompt

                    }

                ]

            },

            timeout=20

        )

        response.raise_for_status()

        data = response.json()

        content = (

            data

            ["choices"]

            [0]

            ["message"]

            ["content"]

        )

        result = json.loads(

            content

        )

        corrected = str(

            result.get(

                "corrected",

                text

            )

        ).strip()

        intent = str(

            result.get(

                "intent",

                "unknown"

            )

        ).strip()

        try:

            confidence = float(

                result.get(

                    "confidence",

                    0

                )

            )

        except (

            TypeError,

            ValueError

        ):

            confidence = 0

        confidence = max(

            0,

            min(

                1,

                confidence

            )

        )

        ambiguous = bool(

            result.get(

                "ambiguous",

                False

            )

        )

        suggestions = (

            result.get(

                "suggestions",

                []

            )

        )

        if not isinstance(

            suggestions,

            list

        ):

            suggestions = []

        cleaned_suggestions = []

        for suggestion in suggestions:

            if not isinstance(

                suggestion,

                dict

            ):

                continue

            suggestion_text = str(

                suggestion.get(

                    "text",

                    ""

                )

            ).strip()

            if not suggestion_text:

                continue

            suggestion_reason = str(

                suggestion.get(

                    "reason",

                    "Alternative possible meaning."

                )

            ).strip()

            try:

                suggestion_confidence = float(

                    suggestion.get(

                        "confidence",

                        0

                    )

                )

            except (

                TypeError,

                ValueError

            ):

                suggestion_confidence = 0

            suggestion_confidence = max(

                0,

                min(

                    1,

                    suggestion_confidence

                )

            )

            cleaned_suggestions.append({

                "text":

                    suggestion_text,

                "reason":

                    suggestion_reason,

                "confidence":

                    suggestion_confidence

            })

        return {

            "available":

                True,

            "corrected":

                corrected or text,

            "intent":

                intent or "unknown",

            "confidence":

                confidence,

            "ambiguous":

                ambiguous,

            "suggestions":

                cleaned_suggestions

        }

    except requests.exceptions.RequestException as e:

        print(

            "Groq API error:",

            e

        )

        return {

            "available":

                False,

            "corrected":

                text,

            "intent":

                "unknown",

            "confidence":

                0,

            "ambiguous":

                False,

            "suggestions":

                []

        }

    except Exception as e:

        print(

            "Semantic engine error:",

            e

        )

        return {

            "available":

                False,

            "corrected":

                text,

            "intent":

                "unknown",

            "confidence":

                0,

            "ambiguous":

                False,

            "suggestions":

                []

        }

# ============================================================

# HOME

# ============================================================

@app.get("/")

def index():

    return render_template(

        "index.html"

    )

# ============================================================

# HEALTH

# ============================================================

@app.get("/health")

def health():

    return jsonify({

        "status":

            "ok",

        "engine":

            "Linguafix Pro 4.0 Enhanced",

        "dictionary":

            dictionary_engine.size(),

        "semantic_ai":

            bool(GROQ_API_KEY),

    })

# ============================================================

# MAIN ANALYZER

# ============================================================

@app.post("/api/analyze")

def analyze():

    body = request.get_json(

        silent=True

    ) or {}

    raw = normalize(

        body.get(

            "text",

            ""

        )

    )

    # ========================================================

    # EMPTY INPUT

    # ========================================================

    if not raw:

        return jsonify({

            "ok":

                True,

            "text":

                "",

            "corrected":

                "",

            "issues":

                [],

            "suggestions":

                [],

            "ambiguous":

                False,

            "message":

                "",

            "intent":

                "unknown",

            "confidence":

                0,

            "engine":

                "Waiting for text",

            "stats":

                stats(

                    "",

                    []

                )

        })

    # ========================================================
    # STEP 0 — SPELLING CORRECTION BEFORE AI
    # ========================================================
    # Correct obvious spelling errors before asking the AI to infer
    # meaning, so typo-filled input does not distort the suggestions.
    pre_spelling_result = spelling_engine.correct_text(raw)
    spelling_corrected_input = pre_spelling_result["text"]
    pre_spelling_issues = pre_spelling_result["issues"]

    # ========================================================
    # STEP 1 — AI SEMANTIC UNDERSTANDING
    # ========================================================
    semantic = semantic_reconstruct(spelling_corrected_input)

    if semantic["available"]:

        semantic_text = (

            semantic["corrected"]

        )

        semantic_suggestions = (

            semantic.get(

                "suggestions",

                []

            )

        )

        semantic_ambiguous = (

            semantic.get(

                "ambiguous",

                False

            )

        )

        semantic_intent = (

            semantic.get(

                "intent",

                "unknown"

            )

        )

        semantic_confidence = (

            semantic.get(

                "confidence",

                0

            )

        )

    else:

        semantic_text = raw

        semantic_suggestions = []

        semantic_ambiguous = False

        semantic_intent = "unknown"

        semantic_confidence = 0

    # ========================================================

    # STEP 1B — TENSE AMBIGUITY GUARD

    # ========================================================

    # If a short sentence such as "i buy laptop" does not contain

    # enough time/tense information, do not allow one arbitrary

    # interpretation to become the only corrected sentence.

    tense_guard = build_tense_ambiguity_suggestions(spelling_corrected_input)

    if tense_guard:

        semantic_text = tense_guard["base"]

        semantic_suggestions = tense_guard["suggestions"]

        semantic_ambiguous = True

        semantic_confidence = min(semantic_confidence, 0.59)

    # ========================================================

    # STEP 2 — LOCAL NORMALIZATION

    # ========================================================

    corrected = fix_spacing(

        semantic_text

    )

    corrected = capitalize_sentences(

        corrected

    )

    issues = capitalization_issues(raw)

    # Keep spelling findings from the original user input visible in the UI.
    issues.extend(pre_spelling_issues)

    # ========================================================

    # STEP 3 — EXISTING LOCAL GRAMMAR

    # ========================================================

    corrected, local_issues = (

        apply_basic_grammar(

            corrected

        )

    )

    issues.extend(

        local_issues

    )

    # ========================================================

    # STEP 4 — EXISTING SPELLING ENGINE

    # ========================================================

    word_result = (

        spelling_engine.correct_text(

            corrected

        )

    )

    corrected = word_result[

        "text"

    ]

    issues.extend(

        word_result[

            "issues"

        ]

    )

    # ========================================================

    # STEP 5 — INTENT

    # ========================================================

    if semantic["available"]:

        intent = semantic_intent

    else:

        intent = (

            intent_engine.detect(

                corrected

            )

        )

    # ========================================================

    # STEP 6 — IMPORTANT:

    # AI SUGGESTIONS HAVE PRIORITY

    # ========================================================

    if (

        semantic["available"]

        and semantic_ambiguous

        and semantic_suggestions

    ):

        unique = _dedupe(

            issues

        )

        return jsonify({

            "ok":

                True,

            "text":

                raw,

            "corrected":

                corrected.rstrip(),

            "issues":

                unique,

            "suggestions":

                semantic_suggestions,

            "ambiguous":

                True,

            "message":

                "Multiple possible meanings were detected. Choose the sentence closest to what you meant.",

            "intent":

                intent,

            "confidence":

                semantic_confidence,

            "engine":

                "AI semantic reconstruction + dictionary + grammar",

            "stats":

                stats(

                    raw,

                    unique

                )

        })

    # ========================================================

    # STEP 7 — OLD LOCAL RECONSTRUCTOR

    #

    # Only used if AI semantic engine is unavailable.

    # ========================================================

    if not semantic["available"]:

        reconstruction = (

            reconstructor.process(

                corrected,

                intent=intent,

                original=raw,

            )

        )

        if reconstruction[

            "ambiguous"

        ]:

            unique = _dedupe(

                issues

            )

            return jsonify({

                "ok":

                    True,

                "text":

                    raw,

                "corrected":

                    corrected.rstrip(),

                "issues":

                    unique,

                "suggestions":

                    reconstruction[

                        "suggestions"

                    ],

                "ambiguous":

                    True,

                "message":

                    reconstruction[

                        "message"

                    ],

                "intent":

                    intent,

                "confidence":

                    0,

                "engine":

                    "Dictionary + grammar + local reconstruction",

                "stats":

                    stats(

                        raw,

                        unique

                    )

            })

        if reconstruction[

            "changed"

        ]:

            corrected = (

                reconstruction[

                    "text"

                ]

            )

            issues.extend(

                reconstruction[

                    "issues"

                ]

            )

    # ========================================================

    # STEP 8 — FINAL PUNCTUATION

    # ========================================================

    corrected, punctuation_issue = (

        end_punctuation(

            corrected

        )

    )

    if punctuation_issue:

        issues.append(

            punctuation_issue

        )

    # ========================================================

    # STEP 9 — FINAL VALIDATION

    # ========================================================

    validation = validate_sentence(

        original=raw,

        corrected=corrected,

        intent=intent,

        dictionary_engine=

            dictionary_engine,

    )

    # ========================================================

    # STEP 10 — VALIDATION SUGGESTIONS

    # ========================================================

    if (

        validation["suggestions"]

        and validation["confidence"] < 0.55

    ):

        unique = _dedupe(

            issues

        )

        return jsonify({

            "ok":

                True,

            "text":

                raw,

            "corrected":

                corrected.rstrip(),

            "issues":

                unique,

            "suggestions":

                validation[

                    "suggestions"

                ],

            "ambiguous":

                True,

            "message":

                "The input has more than one plausible meaning. Choose the sentence closest to your intended meaning.",

            "intent":

                intent,

            "confidence":

                validation[

                    "confidence"

                ],

            "engine":

                "AI semantic reconstruction + dictionary + grammar",

            "stats":

                stats(

                    raw,

                    unique

                )

        })

    # ========================================================

    # STEP 11 — FINAL CONFIDENCE

    # ========================================================

    validation_confidence = validation.get(

        "confidence",

        0

    )

    try:

        validation_confidence = float(

            validation_confidence

        )

    except (

        TypeError,

        ValueError

    ):

        validation_confidence = 0

    final_confidence = max(

        semantic_confidence,

        validation_confidence

    )

    # ========================================================

    # STEP 12 — FINAL RESPONSE

    # ========================================================

    unique = _dedupe(

        issues

    )

    return jsonify({

        "ok":

            True,

        "text":

            raw,

        "corrected":

            corrected,

        "issues":

            unique,

        "suggestions":

            [],

        "ambiguous":

            False,

        "message":

            "",

        "intent":

            intent,

        "confidence":

            round(

                final_confidence,

                2

            ),

        "engine":

            "AI semantic reconstruction + dictionary + grammar",

        "stats":

            stats(

                raw,

                unique

            )

    })

# ============================================================

# DEDUPLICATE ISSUES

# ============================================================

def _dedupe(issues):

    unique = []

    seen = set()

    for item in issues:

        key = (

            item.get(

                "category"

            ),

            item.get(

                "bad"

            ),

            item.get(

                "suggestion"

            ),

            item.get(

                "message"

            ),

        )

        if key not in seen:

            seen.add(

                key

            )

            unique.append(

                item

            )

    return unique

# ============================================================

# START SERVER

# ============================================================

if __name__ == "__main__":

    print(

        "=" * 60

    )

    print(

        "LINGUAFIX PRO 4.0 ENHANCED"

    )

    print(

        "Semantic AI + dictionary + spelling + grammar + intent"

    )

    print(

        "http://127.0.0.1:5000"

    )

    print(

        "=" * 60

    )

    if GROQ_API_KEY:

        print(

            "Semantic AI: ENABLED"

        )

    else:

        print(

            "Semantic AI: DISABLED - GROQ_API_KEY missing"

        )

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=False

    )
