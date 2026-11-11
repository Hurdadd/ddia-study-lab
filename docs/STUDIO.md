# Exercise studio and inline concept labs

Two learning tools sit on top of the DDIA reading experience. Both are static,
local-first and bilingual (Persian RTL / English), with light and dark themes.
All simulated numbers are educational assumptions, not infrastructure benchmarks.

![Studio run: packets flow along the edges and a verdict card appears](media/studio-run.gif)

## Run locally

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open [the studio](http://127.0.0.1:8766/studio/) or any chapter. No API key,
database or build step is needed.

## Inline concept labs (all 14 chapters)

Each chapter has 3 short experiments placed right after the section that explains
the concept (4 in chapter 6): **43 labs**. A lab is a small deterministic state
machine. You pick a decision, advance one event at a time and watch what survives
a crash, a retry or a lagging replica.

![A chapter lab: a write, a held replication message and a stale read](media/chapter-lab.gif)

- Each lab uses one of four layouts (row, stack, fan, triangle) with animated links.
  A message bubble travels between nodes, changed values flash, failed nodes dim.
- Controls: **Next step**, **Play steps**, **Back one step**, **Reset** and
  **Play whole flow**, which plays up to four distinct scenarios start to finish.
- Every lab lists its teaching model and assumptions under the diagram.
- Source: `assets/concept-labs.js` (models), `assets/concept-labs.css`,
  `assets/build_concept_labs.py` (inserts each lab after its teaching section).
- Animations ignore the operating-system reduced-motion setting on purpose, because
  the motion is the content. Set `data-motion="off"` on `<html>` to switch them off.

## Studio workspace

- Choose one of **84 exercises**: 49 chapter exercises and 35 classic system-design problems.
- Add components, click the round source port and then the destination to draw an arrow. Double-click an arrow to edit its label, protocol, endpoints and flow kind.
- Right-click a node, arrow, annotation or blank canvas for contextual editing, duplication, deletion, reversal and undo/redo. Shift+F10 opens the same menu from the keyboard. Notes and pen strokes can be dragged; text notes can be edited.
- Selection, Connect, Pan, Undo and Redo are visible in the canvas toolbar. Components carry category colors and type icons; generated bilingual node names follow the selected language.
- Capacity (including zero), replicas, latency, labels and design notes are editable in Settings.
- **Run** (header, Simulate tab or the pill on the canvas) simulates the selected
  request rate. Packets move along every active edge, receiving nodes glow, and an
  overloaded node drops packets in red. A verdict card says whether the design holds
  the load, names the bottleneck, and offers **Score it**.
- **Solution walkthrough**: the 49 chapter exercises use the authored solution steps, assumptions, worked examples, failure histories, common mistakes, alternatives and answered follow-ups. Their original diagrams open inside the studio; compatible dataflow figures can be copied onto the editable canvas. Classic problems show their individual design hints.
- A reasoning figure is distinct from a request-capacity graph: loading one never invents QPS or latency for version barriers, timing or conditional histories.
- Compare your design with the exercise-specific reference in its own read-only tab.
- Record tradeoffs, annotate the canvas, save designs, export or share them.
- Use the interview timer, the structural evaluation and the local progress dashboard.

Deep links used by the chapters: `studio/index.html?exercise=ch8-ex4` opens one
exercise and `studio/index.html?chapter=8` opens the first exercise of a chapter.

Evaluation reports **reference structure coverage**: component multiplicities (35 points), directed typed connections (35) and component-neighbour roles (30). A reference covers its own criteria at 100%; deleting edges reduces coverage. Equivalent designs can be valid despite lower reference coverage. This is not an automatic correctness grade. Workload results and exercise-specific reasoning questions are separate; generic replica and utilization targets no longer deduct exercise points.

It cannot prove consistency,
correctness, production capacity or readiness for a particular interview level.
Several different designs can satisfy a brief. Reference designs are discussion
sketches, not the only accepted answer; read the linked worked solution too.

Saved designs and progress stay in this browser's local storage. They are not a
cloud account or a backup. Export JSON to keep a portable copy. A shared design
link carries the design in the URL fragment; it is not a live collaborative session.
Do not put private data into a design you share.

## Reference designs

The 49 chapter exercises each have their own reference topology, written in
`assets/exercise_references.py` (nodes, edges, a bilingual note). The catalog builder attaches authored lessons from `assets/solutions/chN/exN.json`. Replica counts are illustrative teaching inputs, not a promise that each design meets every load. The legacy sizing helper produces a separate report; the builder does not consume it. The 35 classic problems keep
the reference topology of the public SysDes project they were adapted from.

## Build and verify

```sh
python3 assets/build_studio_data.py      # catalog: 38 components, 84 exercises
python3 assets/build_concept_labs.py     # inserts the labs into the chapters
npm ci
npm run test:studio
npm run test:studio:browser             # server above + Chrome; PW_CHANNEL may override
node assets/check_concept_labs.cjs
python3 assets/build_site.py
node assets/make_readme_gifs.cjs         # re-records docs/media/*.gif (needs ffmpeg and Chrome)
```

The studio is included in the allowlisted `public/` export; the README GIFs are not.

## Sources and boundaries

The studio's feature set was inspired by the public
[SysDes studio](https://system-dec.vercel.app/studio) and its
[source repository](https://github.com/subhm2004/SysDes). The DDIA implementation
(canvas, engine, labs, walkthrough, layout and styling) is original code for this
project's static, bilingual environment. The 35 classic problems and the component
catalog values are adapted from SysDes data, and that repository publishes no
licence file, so their reuse terms are not confirmed. Browser observations and
extracted evidence are kept as local development records, not published site content.

## Request and background flows

Solid arrows are synchronous request dependencies. Dashed background and control arrows remain editable and count toward reference structure, but are excluded from the request-throughput and latency calculation. Their queue growth, lag, eventual completion and failures require separate histories; the simulator states this explicitly. The generator classifies replication, event consumers and metadata/monitoring flows by component role, and the inspector can change any classification. A failed logical node still takes all of that node’s replicas down; replica count alone does not model automatic failover.

The chapter 6 solution distinguishes log receipt, durability and replay before a replica may serve a read. See the [PostgreSQL synchronous_commit documentation](https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-SYNCHRONOUS-COMMIT).
