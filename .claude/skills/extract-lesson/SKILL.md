---
name: extract-lesson
description: Extract a Maryknoll Taiwanese lesson's vocabulary and example sentences from the scanned PDF into the project's two per-lesson CSVs, then build the Anki decks. Use when the user asks to add/extract a lesson (e.g. "do lesson 14 of book 2, pages 7-17"). Covers rendering pages, transcribing POJ + tone-sandhi numbers from images, the sub-headword promotion convention, and building.
---

# Extract a Maryknoll lesson → CSVs → decks

Turns the vocab + example sentences of one lesson from `Maryknoll_Taiwanese_Book_{N}.pdf` into
`maryknoll-book-{N}/csv/maryknoll_book{N}_lesson{M}_vocab.csv` and `..._vocab_examples.csv`.

Read `CLAUDE.md` first — it holds the **POJ conventions**, the **tone-sandhi rules** (substitution table + the
numbered exceptions, incl. the 1-3-7 enclitic rule), the **CSV schemas**, the **sub-headword** convention, and the
**Taiwanese Hàn-jī (MOE)** table. This skill is the *procedure*; CLAUDE.md is the *reference data*. Apply both.

## 1. Render the pages

The PDFs are **scanned images with no text layer** (`pdftotext` returns nothing) — everything is vision/OCR.

```bash
cd /tmp
pdftoppm -r 300 -f <start> -l <end> /Users/mchaver/Documents/books/taiwanese/Maryknoll_Taiwanese_Book_<N>.pdf /tmp/pg
for f in /tmp/pg-*.ppm; do sips -s format png "$f" --out "${f%.ppm}.png" >/dev/null 2>&1; done
```

300 dpi is worth it — the tiny superscript sandhi numbers are hard to read at 200. To zoom, crop with sips
(`sips -c <h> <w> --cropOffset <y> <x> in.png --out out.png`); halves/thirds of a page are very legible.

## 2. Transcribe — and beware the image-context cap

Capture **every printed superscript sandhi number** above each syllable. Distinguish a circumflex (`â/ê/ô` = tone-5
diacritic) from an actual number. Convert as you go: book `*` → `ⁿ`; `o·` interpunct; tone-8 vertical bar (`chia̍h`).

**Gotcha:** after you've read many images in one session, the API starts rejecting further image reads with a
"many-image request… exceeds 2000px" error (earlier large renders in context now violate the per-image cap). Once this
trips you cannot read more images directly. **Work around it by delegating transcription to subagents** (Agent tool,
`general-purpose`), **one page per agent**, each given the POJ/tone conventions in its prompt. A fresh subagent's
context isn't capped, and several run in parallel. Have each return: headword(s) with superscript numbers, the Chinese
chars, the English gloss, and every sub-headword + example sentence with per-syllable numbers. For a handful of
genuinely ambiguous tokens, spawn a tiny targeted verification agent rather than guessing.

## 3. Write the two CSVs

Follow the schemas in CLAUDE.md exactly. Key points:

- **Vocab** (`number, poj, poj_sandhi, taiwanese_hanji, mandarin, english, notes`): one row per headword. `poj` is base
  (diacritics only, no numbers); `poj_sandhi` applies the substitution table + exceptions. `taiwanese_hanji` is the MOE
  form (keep it word-for-word in sync with `poj`); `mandarin` is a *translation* (often differs from the Hàn-jī).
- **Sub-headwords** (derived words the book lists under a main entry — `a-só`, `cha-bó·-kiáⁿ`, the number readings,
  `chò kang`, …) are **vocabulary, not examples**: put each in the *vocab* file right after its parent and renumber the
  list sequentially in book order (see CLAUDE.md "Sub-headwords"). Only full **sentences** go in the examples file.
- **Examples** (`vocab_number, poj, poj_sandhi, taiwanese_hanji, english`): `vocab_number` is the FK to the (renumbered)
  parent headword.
- **CSV quoting**: RFC 4180 — any field with `,` `"` or newline must be quoted, internal `"` doubled. Malformed quoting
  silently drops/merges rows.

## 4. Register and build

1. Add the lesson number to that book's `lessons` list in `BOOKS` in `build.py` (e.g. `"lessons": [14, 21]`).
2. Build and check the printed counts:

```bash
.venv/bin/python build.py
```

3. Verify integrity — counts match what you expect, and no orphan foreign keys:

```bash
.venv/bin/python - <<'EOF'
import csv
base="maryknoll-book-<N>/csv/maryknoll_book<N>_lesson<M>"
vnums={int(r["number"]) for r in csv.DictReader(open(base+"_vocab.csv"))}
ex=list(csv.DictReader(open(base+"_vocab_examples.csv")))
print("vocab:",len(vnums)," examples:",len(ex),
      " orphans:",sorted({int(r["vocab_number"]) for r in ex}-vnums) or "none")
EOF
```

The build is deterministic, so committing the regenerated `.apkg` files only changes content that actually changed.

## Notes on fidelity

- When a printed tone number contradicts the naive substitution table, the page wins — it's revealing an exception.
- Names/loanwords: use plausible MOE/Hàn-jī and flag guesses to the user.
- Surface judgment calls (uncertain Hàn-jī, a POJ that doesn't map to a standard character, dropped detail) to the user
  rather than silently committing them.
