# taiwanese-anki-decks

This is a curated collection of Taiwanese language Anki decks.

## Building the decks

Decks are generated from CSV source files using [genanki](https://github.com/kerrickstaley/genanki).

### First-time setup

Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Build

```bash
.venv/bin/python build.py
```

This reads the CSVs in `maryknoll-book-1/csv/` and writes twelve `.apkg` files
to `maryknoll-book-1/decks/` — four per lesson:

- `lesson{N}_vocab_hanji_front.apkg` — vocab card, Taiwanese Hanji on the front
- `lesson{N}_vocab_poj_front.apkg` — vocab card, POJ on the front
- `lesson{N}_examples_hanji_front.apkg` — example sentence, Hanji on the front
- `lesson{N}_examples_poj_front.apkg` — example sentence, POJ on the front

Import whichever `.apkg` files you want into Anki via **File → Import**.
Re-running the script after editing CSVs updates existing cards in place
(stable model/deck IDs and per-note GUIDs).
