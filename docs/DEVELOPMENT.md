# Development

Use Python 3.10+ and a static HTTP server. No model keys or database are needed.
The exercise studio and inline chapter experiments also run statically; build
steps, tests and model limits are documented in [STUDIO](STUDIO.md).
Run `python3 assets/build_final_project.py` after editing the capstone generators or
JSON ledgers, then `python3 assets/check_final_project.py` and
`python3 assets/structcheck.py index.html final-project/index.html`.
Run `python3 assets/build_site.py` to create the isolated `public/` export.

## Inline glossary

`assets/glossary.json` is the single source of truth for the technical terms. Each
entry carries a bilingual one-line definition (the hover preview), an everyday
analogy, the technical account, and the trap the analogy usually hides.

    python3 assets/build_glossary.py    # writes glossary/index.html and assets/glossary-data.js
    python3 assets/check_glossary.py    # validates the data, both artefacts and the page wiring

Edit the JSON, never the two generated files. `assets/glossary.js` marks the first
mention of a term inside each chapter section with a dotted underline, previews the
definition on hover or keyboard focus, and links to the entry. Marking is capped at
three per term per language and four per paragraph, so a long chapter does not fill
with marks; add `data-no-glossary` to opt a subtree out. `section` in an entry is
optional: without it the builder anchors the entry to the first chapter section that
mentions the term.

For browser verification use Node 22+, `npm ci`, and `npm run test:browser` with the
local server running on port 8766. Chrome is the default. Alternatively run
`npx playwright install chromium` and set `PW_CHANNEL=chromium`.
`BASE_URL` changes the test origin. Review images stay outside Git.

Preserve the cream/cocoa reading surfaces, Nunito/Vazirmatn typography, pastel accents,
numbered lesson navigation and native disclosures. Test Persian RTL, English LTR,
390px mobile, desktop, dark theme, keyboard and reduced motion together.
The POV is a local educational simulation; never imply it runs a backend.

Frozen Archify HTML must be regenerated through its provenance workflow rather than
hand-edited. The manifest selects nine export/specification hash pairs checked by SHA-256.
The optional Archify generator is not required to serve committed diagrams.

## CI template

`.github/ci-templates/checks.yml` contains the reproducible GitHub Actions job.
It is supplied as an inactive template. Enabling a GitHub Actions workflow requires the appropriate repository permissions.
A maintainer with that permission can move it to `.github/workflows/checks.yml`.
Local checks are executable now; no remote CI pass is claimed.
