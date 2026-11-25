# Chapter 12 content pipeline

The page is generated. Do not edit `ch12-stream-processing/index.html` by hand;
edit the content and rebuild.

## Files

- `template.html` — the page skeleton. Every bilingual block is a placeholder:
  `{{fa:b012}}` or `{{en:b012}}`. Diagrams, labs and tables stay here as raw HTML.
- `content.json` — one record per block:
  ```json
  "b012": { "section": "s1-1", "fa": "<div class=\"fa\">…</div>", "en": "<div class=\"en\">…</div>" }
  ```
- `meta.json` — where the build writes.

## Commands

```bash
npm run build:chapter      # render content/ch12 -> ch12-stream-processing/index.html
npm run check:bilingual    # fail if any block misses fa or en
npm run report:bilingual   # length drift report between fa/en prose
```

## Adding a language

1. Add the language to `EXTRA` in `assets/build_chapter.py` (e.g. `("vi", "zh")`).
2. For each block, add the key to `content.json`:
   `"vi": "<div class=\"vi\">…</div>"`.
3. The build appends it after the English block, so the template never changes.
4. Mark the translation status in the block (`"vi_status": "machine"`) and do not
   advertise it as reviewed until a native speaker signs off.

## Rule

Every block must have every required language. A missing translation fails the
build; it is never silently skipped.
