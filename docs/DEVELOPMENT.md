# Development

Use Python 3.10+ and a static HTTP server. No model keys or database are needed.
The exercise studio and inline chapter experiments also run statically; build
steps, tests and model limits are documented in [STUDIO](STUDIO.md).
Run `python3 assets/build_final_project.py` after editing the capstone generators or
JSON ledgers, then `python3 assets/check_final_project.py` and
`python3 assets/structcheck.py index.html final-project/index.html`.
Run `python3 assets/build_site.py` to create the isolated `public/` export.

## Glossary

`assets/glossary.json` is the single source of truth for the technical terms. Each
entry is written twice (Persian and English) and carries, in this order: a one-line
definition for the hover preview, a jargon-free everyday scene, an analogy, an
optional generated diagram, the technical account, key numbers, longer sections, an
optional comparison table, the usual trap, and related terms.

Every entry also has a `tier`. Tier A must ship a figure and at least one long-form
section; tier B is a full but shorter entry. The floor each tier has to clear is in
`FLOOR` in `assets/build_glossary.py`, and the checker enforces it, so a thin entry
fails the build rather than shipping.

    python3 assets/build_glossary.py    # writes glossary/ and assets/glossary-data.js
    python3 assets/check_glossary.py    # validates data, pages, figures and wiring
    python3 assets/build_glossary.py --preview   # build only the terms that exist

One page for every entry would run to several megabytes, so the glossary is published
as `glossary/index.html` (every term, one row each, searchable) plus
`glossary/ch<N>/index.html` (the full entries for one chapter). Links from a chapter
point at the exact page and anchor. `assets/glossary-data.js` carries only the
one-line definitions, so it stays small enough to load on every chapter page.

Diagrams are generated, not drawn: `assets/figures.py` renders a declared spec
(`split`, `compare`, `pipeline`, `ladder`, `timeline`, `grid`, `ring`, `quorum`,
`bars`) into inline SVG with no colour literals, so light, dark, RTL and LTR all work
and the page stays `file://` safe. `figures.validate()` is the contract; label lengths
are part of it. Add a new kind by adding a renderer and a validation branch together.

`assets/glossary.js` marks the first mentions of a term in a chapter with a dotted
underline, previews the definition on hover or keyboard focus, and links to the entry.
Marking is capped at two per term per language and four per paragraph, so a long
chapter does not fill with marks; add `data-no-glossary` to opt a subtree out.
`section` in an entry is optional: without it the builder anchors the entry to the
first chapter section that mentions the term.

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

## Star counter

`assets/build_stars.py` is the only writer of the star number. It reads the live
stargazer list (`gh api`, falling back to the public API), writes
`assets/stars.json`, redraws `assets/badges/stars.svg` for the README badge row, and
stamps the value into every `[data-star-count]` slot on the home page and the
exercise audit. The same read feeds `assets/star_history.py`, which writes
`assets/star-history.json` and draws `assets/star-history.svg`: a snapshot of the
accounts that currently star the repository, one step per current stargazer,
weekly ticks on a short history and month ticks once the span is longer, with each
month's current additions under the axis. The README labels it a star count
snapshot, not an append-only history. Because the badge and the chart come from one
list, they cannot disagree; `unstar` removes a step, which the API cannot show, so
drops are not represented.

    python3 assets/build_stars.py             # fetch, then refresh JSON, badge and pages
    python3 assets/build_stars.py --offline   # reuse the cached count, redraw only
    python3 assets/build_stars.py --check     # fail when the cache, badge or a slot drifted

The site never calls GitHub: `assets/stars.js` re-reads the same-origin JSON, so a
deployment shows the current count without a third-party request, and the baked
number stays correct with JavaScript off. A live read that comes back as zero is
treated as a failed read, not as an empty repository. A count older than 14 days is
reported by `--check`.

`.github/workflows/stars.yml` runs the command every thirty minutes and commits only
when a byte changed, so one commit per new star or changed stargazer list rather
than one per run. That is why the chart's x-axis ends at the newest star instead of
at "now", and why both writers skip a rewrite when the list is unchanged: a fresh
timestamp on every run would turn a schedule into commit noise. The current number
lives in the badge, the site pill and the JSON, not in the curve's right edge. That
is the freshest a README can be, and the measurement is in the workflow header:

| Served by | Cache header | Worst-case lag in a README |
| --- | --- | --- |
| `raw.githubusercontent.com` (repo-relative assets, what this project uses) | `max-age=300` | about five minutes after the commit |
| `camo.githubusercontent.com` (shields.io, star-history.com and every other remote image) | `max-age=86400` | a day |

So the vendored badge and chart, refreshed by a schedule, stay fresher than the
badge services most repositories embed. The workflow needs the repository setting
*Actions → Workflow permissions → Read and write*, because `GITHUB_TOKEN` cannot be
granted more permission than the repository default; the job asks for `contents:
write` and nothing else.

## CI template

`.github/ci-templates/checks.yml` contains the reproducible GitHub Actions job.
It is supplied as an inactive template. Enabling a GitHub Actions workflow requires the appropriate repository permissions.
A maintainer with that permission can move it to `.github/workflows/checks.yml`.
Local checks are executable now; no remote CI pass is claimed.
