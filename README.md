# taiwanese-anki-decks

A curated collection of Taiwanese (Tâi-gí / Hokkien) Anki decks, generated
from CSV source files. The first deck is built from the Maryknoll Language
Service Center's *Taiwanese Book 1* — vocabulary and example sentences,
each annotated with Taiwanese Hàn-jī, Pe̍h-ōe-jī (POJ) romanization,
tone-sandhi numbering, Mandarin translation, and English gloss.

## Output decks

After running `build.py`, two kinds of artifacts land in
`maryknoll-book-1/decks/`:

**Combined decks** (the ones to import / share):

- `maryknoll_book1_all_hanji_front.apkg` — every vocab and example note,
  Hàn-jī on the front.
- `maryknoll_book1_all_poj_front.apkg` — same notes, POJ on the front.

**Per-lesson decks** (handy during development; can be ignored if you only
want the combined set):

- `lesson{N}_vocab_hanji_front.apkg` / `lesson{N}_vocab_poj_front.apkg`
- `lesson{N}_vocab_examples_hanji_front.apkg` / `lesson{N}_vocab_examples_poj_front.apkg`

The combined decks share GUIDs with the per-lesson decks, so importing
both yields no duplicates.

## Building

First-time setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Build:

```bash
.venv/bin/python build.py
```

The build is **deterministic** — the same CSV input produces byte-identical
`.apkg` output, so git diffs only reflect actual content changes.

## Editing the CSVs

Per-lesson source data lives in `maryknoll-book-1/csv/`:

- `maryknoll_book1_lesson{N}_vocab.csv` — headwords
- `maryknoll_book1_lesson{N}_vocab_examples.csv` — example sentences
  (foreign-keyed to vocab via `vocab_number`)

After editing, re-run `build.py` and the `.apkg` files will update in place
(stable model/deck IDs and per-note GUIDs mean existing cards are updated
rather than duplicated on re-import).

See `CLAUDE.md` for the project's conventions on POJ normalization, tone
sandhi rules, and recommended Taiwanese Hàn-jī forms.

## Attribution

Vocabulary, example sentences, and lesson structure are adapted from
*Maryknoll Taiwanese Book 1*, published by the Maryknoll Language Service
Center, Taichung, Taiwan. The Anki formatting, sandhi numbering scheme, and
build pipeline in this repository are original work.
