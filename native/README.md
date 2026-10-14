# Gem City Data Model Lab

The final student-facing native application is published at `/js/`. It runs with local HTML/CSS/JavaScript only and adds no storage service. The existing site root and original Streamlit implementation remain intact.

Build with `python native/build.py`. Export teaching content with the repository Python interpreter using `python native/export.py`; Python is tooling only and is never loaded by the delivered app. Validate with `node --test native/tests/*.test.mjs`, the original repository tests, ESLint, and `python native/tests/browser.py` after building.

All original seven stages, source tables, normalized schema, E-R and REA diagrams, answer-specific feedback, validation, attempts and revisions are retained. Native controls use distinct earned and viewed stages. Earlier pages are readonly; Back/Forward only traverse reached pages; validation advances the lesson.

Valid original version-2 `progress` links import at `/js/` by retaining their query parameters. The exact 63-bit seed and CPython shuffle ordering are preserved. New native links use version 3, retaining original fields while supporting unfinished revisions and counters beyond the original 99-attempt snapshot limit. Open those links at `/js/`; the original Python/root application does not accept version 3. Refresh and bookmarks preserve native choices, submitted answers, attempts and review position. No central saving is added.

See [VALIDATION.md](VALIDATION.md), [results](review/browser-results.json), and screenshots in `review/`. The accepted Receivables reference is commit `a9dd736614db779b75389222ed8c251dc4d8db8f`; no case-specific teaching changes were copied.
