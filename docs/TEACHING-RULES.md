# Teaching rules for chapter copy

These are the rules used to rewrite Chapter 12. Both languages follow them.

## 1. Start from a problem, not a definition
Name the situation and the stake before the term. "You cannot sort a stream
because the last record may be the smallest" beats "a stream is unbounded".

## 2. One idea per paragraph
If a paragraph needs two "and"s, split it. Jargon gets a plain explanation on
first use, not a translation.

## 3. Examples follow the four questions
Every technical example answers, in order:
1. Who is doing what, and what breaks if nothing is done?
2. What happens, step by step, with numbers or event ids?
3. What does this guarantee — and what does it explicitly not guarantee?
4. What should the reader take away?

## 4. End each section with a question
One question the reader can answer in their own words. It is not a test; it is
a pause. Put the answer behind a details block when the format allows.

## 5. Say what a guarantee does *not* cover
Exactly-once stops at the framework boundary. A watermark is an estimate.
A DLQ without monitoring is lost data. Every claim has an edge; name it.

## 6. Keep both languages on the same skeleton
Same headings, same examples, same order, same claims. Neither language is a
summary of the other. When one changes, the other changes in the same commit;
run `npm run check:bilingual` to see drift.
