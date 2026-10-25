# Linguafix Pro 4.0 Enhanced

This version extends the original conservative correction engine with:

- layered dictionary protection
- chat/abbreviation handling
- technical vocabulary protection
- fuzzy spelling correction
- intent detection
- context-aware sentence reconstruction
- ambiguous-input suggestions
- final validation
- the existing `/api/analyze` endpoint

## Setup

```bash
pip install -r requirements.txt
python app.py
```

Open:

http://127.0.0.1:5000/

## Important

A dictionary tells the system what words can mean. It cannot reliably infer arbitrary user intent by itself. For genuinely open-ended meaning reconstruction, add an NLP/LLM semantic model later. This version deliberately avoids inventing unsupported meaning.
