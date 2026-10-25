/* ============================================================
   LINGUAFIX PRO 4.0
   FRONTEND ANALYSIS ENGINE
   ============================================================ */

"use strict";


/* ============================================================
   ELEMENTS
   ============================================================ */

const input =
    document.getElementById("input");

const analyzeBtn =
    document.getElementById("analyzeBtn");

const clearBtn =
    document.getElementById("clearBtn");

const copyBtn =
    document.getElementById("copyBtn");

const corrected =
    document.getElementById("corrected");

const issuesList =
    document.getElementById("issuesList");

const intentBox =
    document.getElementById("intentBox");

const wordAnalysisBody =
    document.getElementById("wordAnalysisBody");

const rewriteSection =
    document.getElementById("rewriteSection");


/* ============================================================
   SUGGESTIONS SECTION
   ============================================================ */

let suggestionsSection =
    document.getElementById("suggestionsSection");

let suggestionsList =
    document.getElementById("suggestionsList");

let suggestionCount =
    document.getElementById("suggestionCount");


if (!suggestionsSection) {

    suggestionsSection =
        document.createElement("section");

    suggestionsSection.id =
        "suggestionsSection";

    suggestionsSection.className =
        "card suggestions-card hidden";

    suggestionsSection.innerHTML = `
        <div class="card-head">

            <div>
                <strong>
                    Possible meanings
                </strong>
            </div>

            <span
                id="suggestionCount"
                class="pill"
            >
                0 suggestions
            </span>

        </div>

        <div class="suggestions-description">
            More than one plausible meaning was detected.
            Choose the sentence closest to what you intended.
        </div>

        <div
            id="suggestionsList"
            class="suggestions-list"
        ></div>
    `;


    const issuesCard =
        document.querySelector(".issues-card");

    const main =
        document.querySelector("main");


    if (issuesCard) {

        issuesCard.parentNode.insertBefore(
            suggestionsSection,
            issuesCard
        );

    } else if (main) {

        main.appendChild(
            suggestionsSection
        );

    } else {

        document.body.appendChild(
            suggestionsSection
        );

    }

}


suggestionsList =
    document.getElementById(
        "suggestionsList"
    );

suggestionCount =
    document.getElementById(
        "suggestionCount"
    );


/* ============================================================
   HTML ESCAPING
   ============================================================ */

function escapeHtml(value) {

    return String(value ?? "")
        .replace(
            /[&<>"']/g,
            function (character) {

                return {
                    "&": "&amp;",
                    "<": "&lt;",
                    ">": "&gt;",
                    '"': "&quot;",
                    "'": "&#039;"
                }[character];

            }
        );

}


/* ============================================================
   TOKENIZATION
   ============================================================ */

function tokenizeWords(text) {

    return String(text || "")
        .match(/\b[\w'-]+\b/g) || [];

}


/* ============================================================
   WORD NORMALIZATION
   ============================================================ */

function normalizeWord(word) {

    return String(word || "")
        .toLowerCase()
        .trim();

}


/* ============================================================
   COUNTER
   ============================================================ */

function updateCounter() {

    if (!input) {
        return;
    }


    const text =
        input.value.trim();


    const words =
        text
            ? tokenizeWords(text)
            : [];


    const counter =
        document.getElementById(
            "counter"
        );


    if (counter) {

        counter.textContent =
            `${words.length} words · ${text.length} characters`;

    }

}


if (input) {

    input.addEventListener(
        "input",
        updateCounter
    );

}


/* ============================================================
   RESET RESULT
   ============================================================ */

function resetResult() {

    if (corrected) {

        corrected.textContent =
            "Your improved sentence will appear here.";

        corrected.className =
            "result-text empty";

    }


    if (intentBox) {

        intentBox.className =
            "intent-box hidden";

        intentBox.innerHTML =
            "";

    }


    if (suggestionsSection) {

        suggestionsSection.className =
            "card suggestions-card hidden";

    }


    if (suggestionsList) {

        suggestionsList.innerHTML =
            "";

    }


    if (rewriteSection) {

        rewriteSection.className =
            "card rewrite-card hidden";

    }


    if (wordAnalysisBody) {

        wordAnalysisBody.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="empty-state"
                >
                    Run an analysis to inspect individual words.
                </td>
            </tr>
        `;

    }


    if (issuesList) {

        issuesList.innerHTML = `
            <div class="empty-state">
                Run an analysis to see grammar,
                spelling and sentence improvements.
            </div>
        `;

    }


    const engine =
        document.getElementById(
            "engine"
        );


    if (engine) {

        engine.textContent =
            "Waiting for text";

    }


    const score =
        document.getElementById(
            "score"
        );


    if (score) {

        score.textContent =
            "—";

    }


    const issueCount =
        document.getElementById(
            "issueCount"
        );


    if (issueCount) {

        issueCount.textContent =
            "0 issues";

    }


    updateCounter();

}


/* ============================================================
   CLEAR BUTTON
   ============================================================ */

if (clearBtn) {

    clearBtn.addEventListener(
        "click",
        function () {

            if (input) {

                input.value = "";

            }

            resetResult();

            if (input) {

                input.focus();

            }

        }
    );

}


/* ============================================================
   COPY BUTTON
   ============================================================ */

if (copyBtn) {

    copyBtn.addEventListener(
        "click",
        async function () {

            const text =
                corrected
                    ? corrected.textContent.trim()
                    : "";


            if (
                !text ||
                text ===
                "Your improved sentence will appear here."
            ) {

                return;

            }


            try {

                await navigator.clipboard.writeText(
                    text
                );


                const original =
                    copyBtn.textContent;


                copyBtn.textContent =
                    "Copied ✓";


                setTimeout(
                    function () {

                        copyBtn.textContent =
                            original;

                    },
                    1200
                );


            } catch (error) {

                console.error(
                    "Copy failed:",
                    error
                );

            }

        }
    );

}


/* ============================================================
   WORD ANALYSIS
   ============================================================ */

function buildWordAnalysis(
    originalText,
    correctedText
) {

    const originalWords =
        tokenizeWords(originalText);

    const correctedWords =
        tokenizeWords(correctedText);


    const a =
        originalWords.map(
            normalizeWord
        );


    const b =
        correctedWords.map(
            normalizeWord
        );


    const rows = [];


    const dp =
        Array.from(
            {
                length:
                    a.length + 1
            },
            () =>
                Array(
                    b.length + 1
                ).fill(0)
        );


    for (
        let i = a.length - 1;
        i >= 0;
        i--
    ) {

        for (
            let j = b.length - 1;
            j >= 0;
            j--
        ) {

            if (
                a[i] === b[j]
            ) {

                dp[i][j] =
                    1 +
                    dp[i + 1][j + 1];

            } else {

                dp[i][j] =
                    Math.max(
                        dp[i + 1][j],
                        dp[i][j + 1]
                    );

            }

        }

    }


    let i = 0;
    let j = 0;


    while (
        i < a.length ||
        j < b.length
    ) {

        if (
            i < a.length &&
            j < b.length &&
            a[i] === b[j]
        ) {

            const original =
                originalWords[i];


            const fixed =
                correctedWords[j];


            if (
                original !== fixed
            ) {

                rows.push({

                    input:
                        original,

                    normalized:
                        fixed,

                    correction:
                        fixed,

                    type:
                        "Capitalization",

                    status:
                        "Improved"

                });

            } else {

                rows.push({

                    input:
                        original,

                    normalized:
                        original,

                    correction:
                        "—",

                    type:
                        "Word",

                    status:
                        "OK"

                });

            }


            i++;
            j++;

            continue;

        }


        if (
            j < b.length &&
            (
                i >= a.length ||
                dp[i][j + 1] >=
                dp[i + 1][j]
            )
        ) {

            rows.push({

                input:
                    "—",

                normalized:
                    "—",

                correction:
                    correctedWords[j],

                type:
                    "Missing word",

                status:
                    "Added"

            });


            j++;

            continue;

        }


        if (
            i < a.length
        ) {

            rows.push({

                input:
                    originalWords[i],

                normalized:
                    originalWords[i],

                correction:
                    "Removed",

                type:
                    "Extra word",

                status:
                    "Removed"

            });


            i++;

            continue;

        }

    }


    if (
        rows.length === 0
    ) {

        originalWords.forEach(
            function (word) {

                rows.push({

                    input:
                        word,

                    normalized:
                        word,

                    correction:
                        "—",

                    type:
                        "Word",

                    status:
                        "OK"

                });

            }
        );

    }


    return rows;

}


/* ============================================================
   RENDER WORD ANALYSIS
   ============================================================ */

function renderWordAnalysis(
    words
) {

    if (!wordAnalysisBody) {
        return;
    }


    if (
        !Array.isArray(words) ||
        words.length === 0
    ) {

        wordAnalysisBody.innerHTML = `
            <tr>
                <td
                    colspan="6"
                    class="empty-state"
                >
                    No word-level analysis available.
                </td>
            </tr>
        `;

        return;

    }


    wordAnalysisBody.innerHTML =
        words.map(
            function (word, index) {

                const original =
                    word.input ??
                    word.original ??
                    word.word ??
                    "";


                const normalized =
                    word.normalized ??
                    word.normalized_word ??
                    original;


                const correction =
                    word.correction ??
                    word.corrected ??
                    "—";


                const type =
                    word.type ??
                    "Word";


                const status =
                    word.status ??
                    (
                        correction !== "—"
                            ? "Improved"
                            : "OK"
                    );


                return `
                    <tr>

                        <td>
                            ${index + 1}
                        </td>

                        <td>
                            <strong>
                                ${escapeHtml(original)}
                            </strong>
                        </td>

                        <td>
                            ${escapeHtml(normalized)}
                        </td>

                        <td>
                            ${
                                correction === "—"
                                    ? "—"
                                    : `
                                        <span class="suggestion">
                                            ${escapeHtml(
                                                correction
                                            )}
                                        </span>
                                    `
                            }
                        </td>

                        <td>
                            ${escapeHtml(type)}
                        </td>

                        <td>
                            <span class="word-status">
                                ${escapeHtml(status)}
                            </span>
                        </td>

                    </tr>
                `;

            }
        ).join("");

}/* ============================================================
   RENDER DETECTED IMPROVEMENTS
   ============================================================ */

/* ============================================================
   RENDER DETECTED IMPROVEMENTS
   ============================================================ */

/* ============================================================
   RENDER DETECTED IMPROVEMENTS
   ============================================================ */

function renderIssues(
    issues,
    originalText,
    correctedText
) {

    if (!issuesList) {
        return 0;
    }

    const original = String(originalText || "").trim();
    const corrected = String(correctedText || "").trim();

    if (
        !original ||
        !corrected ||
        original.toLowerCase() === corrected.toLowerCase()
    ) {

        issuesList.innerHTML = `
            <div class="empty-state">
                No major improvements detected.
            </div>
        `;

        return 0;
    }

    let detectedIssues = [];

    if (Array.isArray(issues)) {

        detectedIssues = issues
            .map(function (issue) {

                if (typeof issue === "string") {
                    return {
                        type: issue,
                        correction: corrected
                    };
                }

                if (!issue || typeof issue !== "object") {
                    return null;
                }

                return {
                    type:
                        issue.type ||
                        issue.category ||
                        issue.rule ||
                        issue.issue_type ||
                        "Improvement",

                    correction:
                        issue.suggestion ||
                        issue.correction ||
                        issue.corrected ||
                        issue.replacement ||
                        issue.fix ||
                        ""
                };

            })
            .filter(Boolean);
    }

    if (detectedIssues.length === 0) {

        detectedIssues.push({
            type: "Sentence Improvement",
            correction: corrected
        });

    }

    issuesList.innerHTML = detectedIssues.map(function (issue) {

        return `
            <div
                class="issue-item improvement-card"
                tabindex="0"
                role="button"
                aria-label="Detected improvement"
            >

                <div class="improvement-left">

                    <span class="change-label">
                        ISSUE
                    </span>

                    <strong>
                        ${escapeHtml(issue.type)}
                    </strong>

                </div>


                <div class="change-arrow">
                    →
                </div>


                <div class="improvement-right">

                    <span class="change-label">
                        CORRECTION
                    </span>

                    <strong>
                        ${escapeHtml(issue.correction)}
                    </strong>

                </div>

            </div>
        `;

    }).join("");


    /* SAME ANIMATION AS BEFORE */

    const cards =
        issuesList.querySelectorAll(".issue-item");

    cards.forEach(function (card) {

        card.addEventListener(
            "click",
            function () {

                card.classList.remove("selected");
                card.classList.remove("clicked");

                void card.offsetWidth;

                card.classList.add("selected");
                card.classList.add("clicked");

                setTimeout(
                    function () {

                        card.classList.remove("clicked");

                    },
                    450
                );

            }
        );


        card.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" ||
                    event.key === " "
                ) {

                    event.preventDefault();

                    card.click();

                }

            }
        );

    });


    return detectedIssues.length;
}

/* ============================================================
   CONFIDENCE
   ============================================================ */

function formatConfidence(
    value
) {

    let confidence =
        Number(value);


    if (
        !Number.isFinite(confidence)
    ) {

        return "—";

    }


    if (
        confidence <= 1
    ) {

        confidence *= 100;

    }


    confidence =
        Math.max(
            0,
            Math.min(
                100,
                confidence
            )
        );


    return (
        confidence.toFixed(0) +
        "%"
    );

}


/* ============================================================
   RENDER INTENT
   ============================================================ */

function renderIntent(
    data
) {

    if (!intentBox) {
        return;
    }


    const intent =
        data.intent ??
        data.meaning ??
        data.detected_meaning ??
        "";


    const confidence =
        data.confidence ??
        data.intent_confidence ??
        data.intentConfidence;


    if (
        !intent &&
        confidence === undefined
    ) {

        intentBox.className =
            "intent-box hidden";

        return;

    }


    intentBox.className =
        "intent-box";


    intentBox.innerHTML = `
        <div class="intent-title">
            Detected meaning
        </div>

        <div class="intent-text">
            ${escapeHtml(
                intent ||
                "Meaning detected from context."
            )}
        </div>

        <div class="intent-divider"></div>

        <div class="intent-confidence">

            <span>
                Intent confidence
            </span>

            <strong>
                ${formatConfidence(
                    confidence
                )}
            </strong>

        </div>
    `;

}


/* ============================================================
   SUGGESTION NORMALIZATION
   ============================================================ */

function normalizeSuggestion(
    suggestion
) {

    if (
        typeof suggestion === "string"
    ) {

        return {

            text:
                suggestion,

            reason:
                "",

            confidence:
                null,

            intent:
                "Possible meaning"

        };

    }


    if (
        !suggestion ||
        typeof suggestion !== "object"
    ) {

        return null;

    }


    return {

        text:
            suggestion.text ??
            suggestion.sentence ??
            suggestion.corrected ??
            suggestion.meaning ??
            suggestion.suggestion ??
            suggestion.value ??
            "",

        reason:
            suggestion.reason ??
            suggestion.explanation ??
            suggestion.description ??
            "A possible interpretation of your intended meaning.",

        confidence:
            suggestion.confidence ??
            suggestion.score ??
            null,

        intent:
            suggestion.intent ??
            suggestion.meaning_type ??
            suggestion.category ??
            suggestion.type ??
            "Possible meaning"

    };

}


/* ============================================================
   PREMIUM MEANING SUGGESTIONS
   ============================================================ */

function renderSuggestions(
    data
) {

    if (
        !suggestionsSection ||
        !suggestionsList
    ) {

        return;

    }


    let suggestions =
        data.suggestions ??
        data.possible_meanings ??
        data.possibleMeanings ??
        data.alternatives ??
        [];


    if (
        !Array.isArray(suggestions)
    ) {

        suggestions = [];

    }


    suggestions =
        suggestions
            .map(
                normalizeSuggestion
            )
            .filter(
                function (item) {

                    return (
                        item &&
                        item.text &&
                        item.text.trim()
                    );

                }
            );


    const seen =
        new Set();


    suggestions =
        suggestions.filter(
            function (item) {

                const key =
                    item.text
                        .trim()
                        .toLowerCase();


                if (
                    seen.has(key)
                ) {

                    return false;

                }


                seen.add(key);

                return true;

            }
        );


    const ambiguous =
        data.ambiguous === true ||
        data.is_ambiguous === true ||
        suggestions.length > 1;


    if (
        !ambiguous ||
        suggestions.length === 0
    ) {

        suggestionsSection.className =
            "card suggestions-card hidden";


        suggestionsList.innerHTML =
            "";


        if (suggestionCount) {

            suggestionCount.textContent =
                "0 suggestions";

        }


        return;

    }


    suggestionsSection.className =
        "card suggestions-card";


    if (suggestionCount) {

        suggestionCount.textContent =
            `${suggestions.length} ${
                suggestions.length === 1
                    ? "suggestion"
                    : "suggestions"
            }`;

    }


    suggestionsList.innerHTML =
        suggestions.map(
            function (suggestion, index) {

                const confidence =
                    suggestion.confidence !== null &&
                    suggestion.confidence !== undefined
                        ? formatConfidence(
                            suggestion.confidence
                        )
                        : "";


                const rank =
                    index === 0
                        ? "TOP MATCH"
                        : `OPTION ${index + 1}`;


                const icon =
                    index === 0
                        ? "✨"
                        : "💡";


                return `
                    <article
                        class="
                            meaning-card
                            ${
                                index === 0
                                    ? "meaning-card-primary"
                                    : ""
                            }
                        "
                        data-suggestion-index="${index}"
                        tabindex="0"
                        role="button"
                    >

                        <div class="meaning-card-top">

                            <div class="meaning-rank">

                                <span>
                                    ${icon}
                                </span>

                                <span>
                                    ${escapeHtml(
                                        rank
                                    )}
                                </span>

                            </div>

                            ${
                                confidence
                                    ? `
                                        <div
                                            class="
                                                meaning-confidence
                                            "
                                        >
                                            ${escapeHtml(
                                                confidence
                                            )} match
                                        </div>
                                    `
                                    : ""
                            }

                        </div>


                        <div class="meaning-intent">

                            ${escapeHtml(
                                String(
                                    suggestion.intent ||
                                    "Possible meaning"
                                )
                            )}

                        </div>


                        <div class="meaning-sentence">

                            ${escapeHtml(
                                suggestion.text
                            )}

                        </div>


                        <div class="meaning-reason">

                            <span>
                                🧠
                            </span>

                            <span>
                                ${escapeHtml(
                                    suggestion.reason
                                )}
                            </span>

                        </div>


                        <button
                            type="button"
                            class="use-meaning-btn"
                            data-suggestion-index="${index}"
                        >

                            <span>
                                Use this meaning
                            </span>

                            <span class="use-arrow">
                                →
                            </span>

                        </button>

                    </article>
                `;

            }
        ).join("");


    const suggestionOptions =
        suggestionsList.querySelectorAll(
            ".meaning-card"
        );


    /* ========================================================
       SELECT SUGGESTION
       ======================================================== */

    function selectSuggestion(
        option,
        index
    ) {

        const selected =
            suggestions[index];


        if (!selected) {
            return;
        }


        const selectedText =
            String(
                selected.text || ""
            ).trim();


        if (!selectedText) {
            return;
        }


        const originalText =
            window.lastAnalysisData?.text ??
            input?.value ??
            "";


        if (!window.lastAnalysisData) {

            window.lastAnalysisData = {};

        }


        window.lastAnalysisData.corrected =
            selectedText;


        window.lastAnalysisData.selectedSuggestion =
            selectedText;


        window.lastAnalysisData.selectedIntent =
            selected.intent;


        window.lastAnalysisData.ambiguous =
            false;


        if (corrected) {

            corrected.textContent =
                selectedText;


            corrected.className =
                "result-text";


            void corrected.offsetWidth;


            corrected.classList.add(
                "meaning-updated"
            );

        }


        suggestionOptions.forEach(
            function (item) {

                item.classList.remove(
                    "selected"
                );

            }
        );


        option.classList.add(
            "selected"
        );


        const button =
            option.querySelector(
                ".use-meaning-btn"
            );


        if (button) {

            button.classList.add(
                "used"
            );


            button.innerHTML = `
                <span>
                    ✓ Meaning selected
                </span>

                <span class="use-arrow">
                    ✓
                </span>
            `;

        }


        const backendIssues =
            window.lastAnalysisData?.issues ??
            [];


        const newIssueCount =
            renderIssues(
                backendIssues,
                originalText,
                selectedText
            );


        const issueCountElement =
            document.getElementById(
                "issueCount"
            );


        if (issueCountElement) {

            issueCountElement.textContent =
                `${newIssueCount} ${
                    newIssueCount === 1
                        ? "issue"
                        : "issues"
                }`;

        }


        const issuesDashboard =
            document.getElementById(
                "issues"
            );


        if (issuesDashboard) {

            issuesDashboard.textContent =
                newIssueCount;

        }


        const localWordAnalysis =
            buildWordAnalysis(
                originalText,
                selectedText
            );


        renderWordAnalysis(
            localWordAnalysis
        );


        if (issuesList) {

            issuesList.classList.remove(
                "improvements-updated"
            );


            void issuesList.offsetWidth;


            issuesList.classList.add(
                "improvements-updated"
            );

        }


        setTimeout(
            function () {

                if (corrected) {

                    corrected.classList.remove(
                        "meaning-updated"
                    );

                }

            },
            900
        );


        setTimeout(
            function () {

                if (!issuesList) {
                    return;
                }


                const section =
                    issuesList.closest(
                        ".issues-card"
                    );


                if (section) {

                    section.scrollIntoView({
                        behavior:
                            "smooth",

                        block:
                            "center"
                    });

                } else {

                    issuesList.scrollIntoView({
                        behavior:
                            "smooth",

                        block:
                            "center"
                    });

                }

            },
            300
        );

    }


    /* ========================================================
       CARD INTERACTION
       ======================================================== */

    suggestionOptions.forEach(
        function (option, index) {

            option.addEventListener(
                "click",
                function (event) {

                    if (
                        event.target.closest(
                            ".use-meaning-btn"
                        )
                    ) {

                        return;

                    }


                    selectSuggestion(
                        option,
                        index
                    );

                }
            );


            const button =
                option.querySelector(
                    ".use-meaning-btn"
                );


            if (button) {

                button.addEventListener(
                    "click",
                    function (event) {

                        event.preventDefault();

                        event.stopPropagation();


                        selectSuggestion(
                            option,
                            index
                        );

                    }
                );

            }


            option.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Enter" ||
                        event.key === " "
                    ) {

                        event.preventDefault();


                        selectSuggestion(
                            option,
                            index
                        );

                    }

                }
            );

        }
    );

}/* ============================================================
   REWRITE
   ============================================================ */

function renderRewrite(
    data
) {

    if (!rewriteSection) {
        return;
    }


    const rewrite =
        data.rewrite ??
        data.meaning_rewrite ??
        data.improved_meaning;


    if (!rewrite) {

        rewriteSection.className =
            "card rewrite-card hidden";

        return;

    }


    rewriteSection.className =
        "card rewrite-card";


    const originalMeaning =
        document.getElementById(
            "originalMeaning"
        );


    const meaningRewrite =
        document.getElementById(
            "meaningRewrite"
        );


    if (originalMeaning) {

        originalMeaning.textContent =
            data.original ||
            input.value;

    }


    if (meaningRewrite) {

        meaningRewrite.textContent =
            rewrite;

    }

}


/* ============================================================
   STATS
   ============================================================ */

function renderStats(
    stats
) {

    stats =
        stats || {};


    const score =
        document.getElementById(
            "score"
        );


    const words =
        document.getElementById(
            "words"
        );


    const sentences =
        document.getElementById(
            "sentences"
        );


    const characters =
        document.getElementById(
            "characters"
        );


    const unique =
        document.getElementById(
            "unique"
        );


    const issues =
        document.getElementById(
            "issues"
        );


    if (score) {

        score.textContent =
            stats.score ?? "—";

    }


    if (words) {

        words.textContent =
            stats.words ?? 0;

    }


    if (sentences) {

        sentences.textContent =
            stats.sentences ?? 0;

    }


    if (characters) {

        characters.textContent =
            stats.characters ?? 0;

    }


    if (unique) {

        unique.textContent =
            stats.unique_words ??
            stats.unique ??
            0;

    }


    if (issues) {

        issues.textContent =
            stats.issues ?? 0;

    }

}


/* ============================================================
   MAIN ANALYSIS
   ============================================================ */

if (analyzeBtn) {

    analyzeBtn.addEventListener(
        "click",
        async function () {

            const text =
                input
                    ? input.value.trim()
                    : "";


            if (!text) {

                if (input) {
                    input.focus();
                }

                return;

            }


            analyzeBtn.disabled =
                true;


            analyzeBtn.innerHTML =
                "Analyzing…";


            try {

                const response =
                    await fetch(
                        "/api/analyze",
                        {
                            method:
                                "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    text:
                                        text
                                })
                        }
                    );


                let data;

                try {

                    data =
                        await response.json();

                } catch (jsonError) {

                    throw new Error(
                        "The server returned an invalid response."
                    );

                }


                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        `Server error: ${response.status}`
                    );

                }


                if (!data.ok) {

                    throw new Error(
                        data.error ||
                        "Analysis failed."
                    );

                }


                window.lastAnalysisData =
                    data;


                window.lastAnalysisData.text =
                    text;


                const finalCorrected =
                    data.corrected ??
                    data.corrected_text ??
                    data.text ??
                    text;


                if (corrected) {

                    corrected.textContent =
                        finalCorrected;


                    corrected.className =
                        "result-text";

                }


                renderStats(
                    data.stats || {}
                );


                const engine =
                    document.getElementById(
                        "engine"
                    );


                if (engine) {

                    engine.textContent =
                        data.engine ||
                        "Linguafix NLP Engine";

                }


                const backendIssues =
                    Array.isArray(
                        data.issues
                    )
                        ? data.issues
                        : [];


                const issueCount =
                    renderIssues(
                        backendIssues,
                        text,
                        finalCorrected
                    );


                const issueCountElement =
                    document.getElementById(
                        "issueCount"
                    );


                if (issueCountElement) {

                    issueCountElement.textContent =
                        `${issueCount} ${
                            issueCount === 1
                                ? "issue"
                                : "issues"
                        }`;

                }


                const issuesDashboard =
                    document.getElementById(
                        "issues"
                    );


                if (issuesDashboard) {

                    issuesDashboard.textContent =
                        issueCount;

                }


                renderIntent(
                    data
                );


                renderSuggestions(
                    data
                );


                const backendWordAnalysis =
                    data.word_analysis ??
                    data.words_analysis ??
                    data.wordAnalysis;


                if (
                    Array.isArray(
                        backendWordAnalysis
                    ) &&
                    backendWordAnalysis.length
                ) {

                    renderWordAnalysis(
                        backendWordAnalysis
                    );

                } else {

                    const localWordAnalysis =
                        buildWordAnalysis(
                            text,
                            finalCorrected
                        );


                    renderWordAnalysis(
                        localWordAnalysis
                    );

                }


                renderRewrite(
                    data
                );

            } catch (error) {

                console.error(
                    "Linguafix error:",
                    error
                );


                if (corrected) {

                    corrected.textContent =
                        "Unable to analyze the text.";

                    corrected.className =
                        "result-text empty";

                }


                const engine =
                    document.getElementById(
                        "engine"
                    );


                if (engine) {

                    engine.textContent =
                        "Analysis error";

                }


                if (issuesList) {

                    issuesList.innerHTML = `
                        <div class="empty-state">
                            ${escapeHtml(
                                error.message ||
                                "Could not connect to the Flask backend."
                            )}
                        </div>
                    `;

                }

            } finally {

                analyzeBtn.disabled =
                    false;


                analyzeBtn.innerHTML =
                    'Analyze meaning <span>→</span>';

            }

        }
    );

}


/* ============================================================
   CTRL + ENTER
   ============================================================ */

if (input) {

    input.addEventListener(
        "keydown",
        function (event) {

            if (
                event.ctrlKey &&
                event.key === "Enter"
            ) {

                event.preventDefault();


                if (analyzeBtn) {

                    analyzeBtn.click();

                }

            }

        }
    );

}


/* ============================================================
   INITIALIZE
   ============================================================ */

updateCounter();


console.log(
    "LinguaFix Pro 4.0 frontend loaded successfully."
);