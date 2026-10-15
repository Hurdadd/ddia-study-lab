# Solutions source schema — ddia-study worked answers

One JSON file per chapter: `assets/solutions/chN.json` (N = 1..14).
`assets/build_solutions.py` renders `ch<folder>/solutions.html` from it.
Diagrams live at `ch<folder>/diagrams/sol<number>-<slug>.html` (hand-built
Tiimo-light SVG pages, same chrome as `nfr-pillars.html`; must pass
`python3 assets/fitcheck.py`).

Split-file layout (preferred for parallel authorship): a directory
`assets/solutions/chN/` with `meta.json` (chapter fields only) plus one
`ex<N>.json` per exercise (solution fields only). The builder merges them;
a single `chN.json` with all fields also works. Never hand-edit the built
`ch*/solutions.html` — rebuilds overwrite it.

## Top-level fields

| field | meaning |
|---|---|
| `chapter` | number 1..14 |
| `exercises_anchor` | section id of the exercise list in the chapter page (e.g. `s7`) |
| `hero_fa` / `hero_en` | hero lede (1–2 sentences) |
| `prev` / `next` | `{"href": ..., "fa": ..., "en": ...}` doc-nav links |
| `solutions` | array, one object per exercise, ordered by number |

Chapter title, folder and hue are taken from `assets/exercise-audit.json`
(single source of truth); a mismatch fails the build.

## Solution fields

Text fields come in `_fa` / `_en` pairs with identical structure (same
number of steps, same headings). Both are raw HTML fragments using only:
`p ol ul li b code pre span table thead tbody tr th td details summary`.
No `h1/h2/h3`, no inline styles, no remote URLs. Persian prose + English
technical terms in `<span class="ltr">` / `<code>`.

| field | required | meaning |
|---|---|---|
| `number` | yes | exercise number; anchor becomes `sol-<number>` |
| `slug` | yes | ascii, used in the diagram filename |
| `interview_q_fa/en` | yes | the bounded interview question (1 paragraph) |
| `answer_fa/en` | yes | 60-second answer: choice + reason + top trade-off |
| `assumptions` | yes | `[{"fa","en"}]` — scale, units, teaching numbers, unknowns |
| `mental_fa/en` | yes | mental model before jargon |
| `steps` | yes | `[{"t_fa","t_en","fa","en"}]` — titled reasoning steps |
| `design_fa/en` | no | components, API/schema/index/partition key, read/write path |
| `worked_fa/en` | no | worked numbers: data, result, units, interpretation |
| `alternatives` | no | `[{"fa","en"}]` — when another choice wins + its cost |
| `failures` | no | `[{"fa","en"}]` — crash/timeout/dup/concurrency/partition cases |
| `code` | no | `{"lang","code","run_fa","run_en","expected_fa","expected_en","status"}`; `lang` is ALWAYS `java` (stdlib only unless the run guide names the dependency); `status` is `verified` (compiled and run here with `javac`/`java`, real output pasted) or `not-executed` (local-run guide only — never claim execution) |
| `tests_fa/en` | no | invariants, failure tests, latency/lag metrics + how to measure |
| `followups` | yes | `[{"q_fa","q_en","a_fa","a_en","level":"senior"/"staff"}]` — every audit follow-up answered, plus added ones |
| `mistakes` | yes | `[{"fa","en"}]` — why each is wrong |
| `diagram` / `diagrams` | yes | single `diagram` or ordered `diagrams` array (see Diagram thread below) |
| `narration` | yes, with single `diagram` | `{"scenario_fa/en","steps":[{"fa","en"}],"point_fa/en","failure_fa/en","guarantee_fa/en","nonguarantee_fa/en"}` — the 8 teacher moves |
| `selfcheck` | yes, with single `diagram` | `{"q_fa","q_en","a_fa","a_en"}` rendered as a `<details>` quiz |
| `sources` | yes | keys of `SOURCES` in `build_exercise_audit.py` |
| `lab_fa/en` | no | pointer to the extended lab and what it adds |

## Diagram thread: step by step, then assembled

Never cram a multi-part argument into one figure. Each solution carries an
ordered reasoning thread:

1. **Step diagrams** (1–3): one figure per major reasoning step, in the same
   order as the `steps`. Each is small and has one job.
2. **Assembly diagram** (1, last): puts the steps together and is the only
   figure allowed to show the whole. Short calculation exercises may have
   just the assembly (a plot/table IS the assembly there).

With the `diagrams` array, every entry carries its own narration and
self-check quiz:
`{"file","made","source","kind_fa","kind_en","caption_fa","caption_en","height","narration":{...8 moves...},"selfcheck":{...}}`.

## Diagram sources

Committed diagram specifications are in `assets/diagram-specs/`. Each generated
solution references its specification through the `source` field. The exported
HTML is committed for static hosting. Re-rendering a diagram requires its generator;
serving existing exports does not. Geometry, labels and provenance hashes must stay
consistent. Raw local tool reports are not publication artifacts.

Rules: no empty headings (omit absent optionals); short calculation
exercises stay short; architecture exercises must have design + failures;
hands-on exercises must have runnable `code` + local-run guide; teaching
numbers are labelled آموزشی, never benchmarks; no company-question claims;
examples neutral and generic.

## Method and numerical rationale

Every solution requires `reasoning_fa` and `reasoning_en` HTML fragments. Explain why the chosen model or formula fits this exercise, define units, distinguish measured values from teaching inputs, and explain how changed assumptions affect the decision. A target is not justified merely by allocating a budget beneath it. These fields render directly after assumptions and are required by the coverage gate.
