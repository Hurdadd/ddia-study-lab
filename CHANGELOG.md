# Changelog

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
