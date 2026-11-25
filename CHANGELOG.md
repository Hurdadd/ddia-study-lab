# Changelog

## Unreleased

- The star count now keeps itself current. `.github/workflows/stars.yml` runs
  `assets/build_stars.py` every thirty minutes and commits only when the number moved,
  so the badge, the chart and the site pill follow new stars without a human. The
  workflow header records the measurement behind that choice: repo-relative assets come
  from `raw.githubusercontent.com` with `max-age=300`, while remote images (shields.io,
  star-history.com) are served through camo with `max-age=86400`, so a scheduled commit
  is fresher than the badge services it replaces.
- The README chart alt text no longer carries a fixed count, so it cannot drift from the
  image. Enabling the workflow required the repository default *Workflow permissions* to
  become read-and-write; the job itself asks only for `contents: write`.
- The site and the README now show the repository's star count. `assets/build_stars.py`
  reads the live stargazer count once per build, draws `assets/badges/stars.svg` for the
  README badge row, and stamps the number into the header and hero star links;
  `assets/stars.js` then refreshes it from a same-origin JSON file, so no visitor request
  ever reaches GitHub and the baked number stays correct with JavaScript off. A live read
  that returns zero is treated as a failed read rather than as an empty repository.
- `/star` and `/stargazers` now redirect to the repository, and the capstone's GitHub link
  points at `ddia-study-lab` instead of the pre-rename `own-the-stack` URL. GitHub still
  answers that old name with a rename redirect, but the project no longer depends on it.
- The README now carries a star-history chart. `assets/star_history.py` collects every
  current stargazer's `starred_at`, writes `assets/star-history.json`, and draws
  `assets/star-history.svg`: a step per star, weekly ticks for a short history and month
  ticks once it spans a year, with each month's additions under the axis. It is redrawn
  by the same command as the badge from the same read, so the number in the badge, the
  number in the site header and the chart's last step are always the same value.
- Documented the refresh (`docs/DEVELOPMENT.md`) and shipped the weekly refresh as the
  inactive `.github/ci-templates/stars.yml` template, alongside the existing checks one.
- Reference designs in the exercise studio now read as architectures instead of a
  strip of cards. Each one is laid out in one column per dependency depth, a column
  of several nodes is centred on its band instead of hanging from the top, and a
  chain longer than six columns continues on a second band whose crossing arrows
  travel below the first. Component names too wide for one line wrap onto two at a
  word boundary, so a card no longer reads half a sentence and an ellipsis.
- The canvas stopped labelling every hop with its transport. A dashed arrow now
  carries its flow kind in the reader's language — `async`, `control` — once per
  fan-out, and the protocol stays in Settings and in the arrow's tooltip. An authored
  edge label still wins, so lesson figures and saved designs render as written.
- The reference tab prints the exercise's rationale as a caption under the read-only
  badge, so the diagram arrives with the reason it is shaped that way.
- Topology, edge kinds, replica counts and the 100% self-coverage the checker asserts
  are unchanged: this release changes layout, labels and captions only.
- The glossary grew from 39 terms to 287, one for every technical term the Persian
  chapters actually use, and every entry got deeper. Each one now runs: a jargon-free
  everyday scene, an analogy, a generated diagram, the technical account, key
  numbers, one or more long-form sections, an optional comparison table, the usual
  trap, and related terms. Entries carry a tier: tier A must ship a figure and at
  least one section, tier B is a full but shorter entry, and the checker refuses an
  entry that falls below its floor.
- Diagrams are generated, not drawn. `assets/figures.py` renders a declared spec into
  inline SVG in nine shapes — split, compare, pipeline, ladder, timeline, grid, ring,
  quorum, bars — with no colour literals, so light, dark, RTL and LTR all work and the
  page stays `file://` safe. 223 entries carry one; label lengths and structure are
  validated before the page is written.
- One page for 284 entries would be several megabytes, so the glossary is published
  as an index (`glossary/index.html`) plus one page per chapter
  (`glossary/ch<N>/index.html`). The index lists every term on one line, searchable in
  both languages; the chapter pages carry the full entries, a pager and a "see in
  context" link into the chapter itself. Chapter marks now resolve to the exact page
  and anchor.
- `assets/glossary-data.js` keeps only the hover definitions (128 KB), so every
  chapter page can load it. Marking stays capped at two mentions per term per
  language, and the hover now advertises the diagram too.
- The homepage gained a glossary band with the live term count, and
  `assets/check_glossary.py` now fails if that number drifts from the data.
- Three hubs were added after the vocabulary audit: `join` (two inputs, one
  result), `hash` (a key to a bucket) and `snapshot` (one consistent instant), plus
  synonym aliases so `partition`, `job`, `JSON` and `Lamport` resolve to the entry
  that already explains them.
- `assets/check_glossary.py` checks the index, every chapter page, every card, every
  figure caption, every marker definition, every internal link and every chapter
  page's asset wiring.

- Added a 39-term bilingual glossary at `glossary/index.html`. Every entry is written
  twice: an everyday analogy first, then the technical account, then the trap the
  analogy hides. Each term also carries a one-sentence definition used by the hover
  preview, and entries link back to the first chapter section that mentions them.
- Chapters now mark the first mentions of a technical term with a dotted underline:
  hovering (or keyboard focus) previews the definition in the current language, and
  clicking opens the entry. Marking is deliberately sparse — three per term per
  language and four per paragraph — and skips code, links, diagram stages, compact
  metadata rows and the exercise studio.
- `assets/glossary.json` is the single source of truth; `python3 assets/build_glossary.py`
  writes both the page and the hover data, and `python3 assets/check_glossary.py`
  fails when the committed artefacts, the entry anchors or the page wiring drift.
  `build_site.py` publishes the new directory and the sitemap includes it.

## 0.4.0 — 2026-10-20

- Rewrote the whole study set in the "friend explaining system design" voice:
  all fourteen chapter pages, all forty-nine worked solutions and the capstone
  workshop. Direct address, everyday Persian, short sentences and one memorable
  punchline per answer.
- Facts, numbers, units, English technical terms, code and program output are
  unchanged. A structural guard checked the HTML tag sequence, every numeric
  literal (Persian and Latin), every `<code>` payload and the half-space count
  on every rewritten file; the reviewed exercise briefs, the headings, the
  anchors and the navigation stayed byte-identical.
- The capstone prose lives in the build sources, so the rewrite covers
  `assets/build_final_project*.py` together with the workshop, recovery,
  interview-evidence, acceptance and chapter-coverage ledgers and the fifteen ADR
  documents. The next build reproduces the new voice instead of reverting it.
- Added the flash-sale inventory exercise to chapter 8: a bounded SKIP LOCKED
  pool, correct lock order and a single-database transaction, with a worked
  solution, a verified Java simulator (6/6 checks) and three hand-made diagrams.
- Added the table-less outbox exercise to chapter 8: state and event in one
  COMMIT with no outbox table, `pg_logical_emit_message`, Debezium and a custom
  SMT, with a worked solution, a verified Java simulator and the SeatGeek
  pipeline diagram.
- Added five industry-case figures with their teacher walkthroughs: Together AI
  cache-aware disaggregated inference (ch2), Databricks billion-scale vector
  search (ch4), the Discord message-store migration timeline (ch6), the Figma
  two-phase live reshard rollout (ch7) and the SeatGeek table-less outbox (ch8).
- Registered the two new chapter 8 exercises in the audit: 49 reviewed exercises
  (25 core, 21 role-specific, 3 supplementary) with a rebuilt audit page, the
  priority SVG and the roadmap counts.
- Extended the capstone evidence register with the Together AI, Databricks, Figma,
  Discord and SeatGeek engineering cases, each labelled as a reported engineering
  problem rather than an interview prompt.
- Fixed two copy-paste placeholders in the worked solutions: chapter 4's vector
  search steps had three different titles sharing one body, and chapter 12's
  third solution had one failure and guarantee text repeated across three
  figures. Each now answers its own question.
- Added an audit gate that fails when the reviewed follow-up question drifts away
  from the worked solution that answers it.

## 0.3.0 — 2026-10-18

- Renamed the repository to `ddia-study-lab` and the site to
  `ddia-study-lab.vercel.app` so "DDIA" is in the name and URL; the old
  `own-the-stack.vercel.app` host now redirects permanently.
- Added `robots.txt`, a generated `sitemap.xml` and per-page title, description,
  canonical, Open Graph / Twitter tags and JSON-LD (`assets/seo_meta.py`, applied
  by `build_site.py`) for all chapters, solutions, the capstone and the audit.
- Added `WebSite` and `Course` structured data and a keyword-first title on the
  home page.

## 0.2.1 — 2026-10-18

- Removed the site-wide `X-Robots-Tag: noindex` header left over from the private
  phase so search engines can index the public site.
- Added Open Graph / Twitter card metadata, a canonical URL and a 1200×630 share
  image (`assets/og-image.png`).
- Added "Star on GitHub" links to the site header, hero and footer.
- Added a search-friendly summary line and a star/share note to the README.

## 0.2.0 — 2026-10-18 (public release)

- Made the GitHub repository public after a full content audit: no credentials,
  secrets, private paths or personal data in tracked files or history
  (`check_publication.py` PASS over 557 files; `.env*` and `.vercel/` ignored).
- Rebuilt the README: live-site hero, 14-chapter roadmap with diagram counts,
  mermaid platform map, 6-step capstone guide, honesty box (proposed vs.
  implemented) and relative links that work on GitHub, Vercel and localhost.
- Aligned GOVERNANCE, SECURITY, CONTRIBUTING, HOSTING, RECOVERY and the
  capstone signature note with public repository access.

## 0.1.0 — 2026-10-15 (private initial release)

- Fourteen bilingual study chapters and an AI-platform design workshop.
- Product introduction, public interview evidence ledger and explicit evidence grades.
- Fifteen ADRs, editable workload estimates and architecture/UML references.
- Selected RPO/RTO contracts with assumptions and planned recovery drills.
- User-controlled request flow and a synthetic developer POV walkthrough.
- Authorship, AGPL-3.0-only licensing, contribution/governance/security policies,
  portable static export and private-deployment instructions.

Platform services, measured SLOs and actual disaster-recovery drills remain future work.

## 0.1.1 — 2026-10-15

- Redesigned the README with a branded SVG cover, bilingual introduction, guided
  navigation, capability/recovery tables and collapsible contributor details.
- Made the production website public at the maintainer’s request; retained the
  private GitHub repository and protected preview/generated deployment URLs.
- Updated deployment, security and ownership wording to match public site access.
