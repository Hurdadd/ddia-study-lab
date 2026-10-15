# Own the Stack

**Make Your Own AI Platform.**

Written, designed, and maintained by **hurdad ashouri** · [@Hurdadd](https://github.com/Hurdadd)

A bilingual Persian/English distributed-systems study lab and an evidence-led AI
platform design workshop. Start with the developer’s problem, estimate the
workload, defend decisions, draw the flows, and define recovery tests before
claiming a production system.

**Current release: an educational website and interactive design prototype.**
The platform APIs, workers, database, CDC pipeline, model serving, real evaluations,
and disaster-recovery automation are not implemented. The repository and deployment
are intentionally private for this initial release; licensing prepares the project
for future sharing and does not make it public.

## Explore

- [Study home](index.html): fourteen chapters inspired by *Designing Data-Intensive
  Applications, 2nd Edition* (Martin Kleppmann and Chris Riccomini).
- [Understand the project](final-project/index.html#overview): product, audience,
  inputs/outputs, synthetic investigation scenario, and scope.
- [Public interview evidence](final-project/index.html#company-evidence): attributed
  accounts with role, date where available, evidence grade, and limitations.
- [Design workshop](final-project/index.html#start-here): seven guided stages.
- [Estimates](final-project/index.html#estimates) and [15 ADRs](final-project/adrs):
  editable arithmetic and explicit rationale, assumptions, validation, and revisit triggers.
- [Recovery objectives](final-project/index.html#recovery): RPO/RTO by failure domain.
- [Summary and developer POV](final-project/index.html#outcome): local, user-controlled
  product simulation with a worker-interruption/recovery story.

## What the proposed platform would do

A developer registers an AI application, submits a run, and retrieves a result
and trace. Shared capabilities provide authorized live context, durable execution,
model routing/budgets, and evaluation/release controls. The initial sample app
investigates synthetic incidents with read-only tools. A later cited-answer app
should reuse the same core. Training a foundation model from scratch and a
multi-GPU training scheduler are outside the first slice.

| Design scenario | RPO objective | RTO objective | Boundary |
| --- | --- | --- | --- |
| Worker process crash | 0 acknowledged state lost | 2 minutes | DB and disk survive |
| Database/disk loss | ≤5 minutes | ≤30 minutes | Synthetic pilot; ≤10GB; independent backup + WAL |
| Whole-region loss | ≤15 minutes | ≤4 hours | Cold recovery; cross-region backup/WAL; current IAM |
| Derived retrieval index | 0 source data lost | ≤4 hours | Authoritative source intact; one-million-document scenario |

These are **selected design objectives, not measured results or hosting SLAs**.
See [recovery contracts](final-project/recovery.json) and the [drill guide](docs/RECOVERY.md).
Only the audience decision is accepted; technical ADRs remain proposed.

## Run locally

Requires Python 3.10+; no application dependencies or API keys are needed.

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open <http://127.0.0.1:8766/>. Fonts are requested from Google Fonts; offline use
falls back to installed fonts. The calculators and animations send no model or
platform requests. Motion starts on request and supports pause, stepping,
keyboard operation, and reduced-motion preferences.

## Build and check

Committed HTML is usable as-is. Rebuild the capstone after changing its source:

```sh
python3 assets/build_final_project.py
python3 assets/check_final_project.py
python3 assets/structcheck.py index.html final-project/index.html
python3 assets/build_site.py
```

`public/` is the deployment artifact. Its allowlist excludes local history,
review captures, credentials, generator state, and tool caches. Existing diagram
exports are committed; regenerating them uses the optional Archify tool and is
not required to run the website. Frozen capstone candidates/receipts are retained
so the static checker can verify their provenance hashes.

Optional browser checks require Node.js, installed Chrome and the pinned
Playwright development dependency:

```sh
npm ci
npm run test:browser
```

Start the local server first. Set `BASE_URL` for another origin and
`PW_CHANNEL=chromium` to use Playwright’s installed Chromium. Screenshots are
written to the ignored review directory. See [development](docs/DEVELOPMENT.md).

## Repository map

```text
assets/          shared styles, browser scripts, generators, checks
ch*/             fourteen bilingual study chapters and diagrams
final-project/   capstone site, ADRs, estimates, recovery and source ledgers
docs/            development, recovery, privacy/deployment, provenance
.github/         contribution templates, ownership and CI
```

## Contributing and governance

Read [CONTRIBUTING](CONTRIBUTING.md), [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md),
[SECURITY](SECURITY.md), [SUPPORT](SUPPORT.md), and [GOVERNANCE](GOVERNANCE.md).
Keep proposed architecture separate from implemented behavior and targets separate
from observations. Source company/interview claims and preserve uncertainty.
Changes require review by the maintainer; private access is by invitation.

There is no CLA or mandatory copyright assignment. Contributions must be yours to
submit and carry the applicable repository license; use a `Signed-off-by` line
under the [Developer Certificate of Origin](DCO).

## Deployment and privacy

See [DEPLOYMENT](docs/DEPLOYMENT.md). Deploy only after enabling Vercel Authentication
for **all deployments**, with no public exceptions. A private GitHub repository
alone does not protect a website. Verify anonymous access to the root, capstone,
and direct assets is denied. Do not publish a share/bypass URL. Public launch is
a separate, explicit decision.

## License and attribution

Original project work: [GNU AGPL-3.0-only](LICENSE), copyright © 2026
**hurdad ashouri**. Preserve notices and comply with the license when conveying or
modifying covered work, including applicable network-source obligations.

The book, linked interview accounts, externally loaded fonts, and embedded
third-party diagram/font code retain their own rights and licenses. See [NOTICE](NOTICE)
and [third-party provenance](docs/THIRD_PARTY.md). This is an independent study
project, not an official O’Reilly, author, employer, or interview-question product.

## فارسی

این پروژه دفتر مطالعه و طراحی یک پلتفرم AI است: معرفی مسئله، ۱۴ فصل، تخمین،
ADR، نمودار، قرارداد بازیابی و نمایش تعاملی از دید توسعه‌دهنده. سرویس‌های خودِ
پلتفرم هنوز پیاده نشده‌اند. نویسنده و نگهدارنده: **hurdad ashouri**.
مخزن و دیپلوی فعلاً خصوصی‌اند؛ مجوز کار اصیل پروژه AGPL-3.0-only است.

The GitHub Actions job is supplied in `.github/ci-templates/checks.yml`; activation
requires a credential with `workflow` scope. It is currently inactive.
