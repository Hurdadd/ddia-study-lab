# Changelog

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
