#!/usr/bin/env python3
"""Build Anki deck package (.apkg) from Maryknoll Book 1 CSV data.

For each lesson, emits four decks:
  - Vocab (Hanji front)
  - Vocab (POJ front)
  - Examples (Hanji front)
  - Examples (POJ front)

Usage:
    .venv/bin/python build.py

Output:
    maryknoll_book1.apkg
"""
from __future__ import annotations

import csv
from pathlib import Path

import genanki

ROOT = Path(__file__).parent
CSV_DIR = ROOT / "csv"
OUT_FILE = ROOT / "maryknoll_book1.apkg"

LESSONS = [1, 2, 3]

MODEL_ID_VOCAB_HANJI = 1607390001
MODEL_ID_VOCAB_POJ = 1607390002
MODEL_ID_EX_HANJI = 1607390003
MODEL_ID_EX_POJ = 1607390004

DECK_ID_BASE = 2059400000

CSS = """
.card {
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  font-size: 22px;
  text-align: center;
  color: #222;
  background: #fafafa;
  padding: 1em;
}
.front-big { font-size: 42px; margin: 0.5em 0; }
.poj { font-family: "Charis SIL", "Noto Serif", serif; }
.sandhi { color: #555; font-size: 18px; }
.mandarin { color: #666; }
.english { color: #333; }
.notes {
  color: #888;
  font-size: 15px;
  font-style: italic;
  margin-top: 1em;
  text-align: left;
  padding: 0 1em;
}
hr { margin: 1em 0; border: 0; border-top: 1px solid #ddd; }
"""

VOCAB_FIELDS = [
    {"name": "number"},
    {"name": "poj"},
    {"name": "poj_sandhi"},
    {"name": "taiwanese_hanji"},
    {"name": "mandarin"},
    {"name": "english"},
    {"name": "notes"},
]

EXAMPLE_FIELDS = [
    {"name": "vocab_number"},
    {"name": "poj"},
    {"name": "poj_sandhi"},
    {"name": "taiwanese_hanji"},
    {"name": "english"},
]

VOCAB_BACK = """{{FrontSide}}
<hr>
<div class="poj">{{poj}}</div>
<div class="poj sandhi">{{poj_sandhi}}</div>
<div>{{taiwanese_hanji}}</div>
<div class="mandarin">{{mandarin}}</div>
<div class="english">{{english}}</div>
{{#notes}}<div class="notes">{{notes}}</div>{{/notes}}
"""

EXAMPLE_BACK = """{{FrontSide}}
<hr>
<div class="poj">{{poj}}</div>
<div class="poj sandhi">{{poj_sandhi}}</div>
<div>{{taiwanese_hanji}}</div>
<div class="english">{{english}}</div>
"""

vocab_hanji_model = genanki.Model(
    model_id=MODEL_ID_VOCAB_HANJI,
    name="Maryknoll Vocab (Hanji front)",
    fields=VOCAB_FIELDS,
    templates=[{
        "name": "Card",
        "qfmt": '<div class="front-big">{{taiwanese_hanji}}</div>',
        "afmt": VOCAB_BACK,
    }],
    css=CSS,
)

vocab_poj_model = genanki.Model(
    model_id=MODEL_ID_VOCAB_POJ,
    name="Maryknoll Vocab (POJ front)",
    fields=VOCAB_FIELDS,
    templates=[{
        "name": "Card",
        "qfmt": '<div class="front-big poj">{{poj}}</div>',
        "afmt": VOCAB_BACK,
    }],
    css=CSS,
)

example_hanji_model = genanki.Model(
    model_id=MODEL_ID_EX_HANJI,
    name="Maryknoll Example (Hanji front)",
    fields=EXAMPLE_FIELDS,
    templates=[{
        "name": "Card",
        "qfmt": '<div class="front-big">{{taiwanese_hanji}}</div>',
        "afmt": EXAMPLE_BACK,
    }],
    css=CSS,
)

example_poj_model = genanki.Model(
    model_id=MODEL_ID_EX_POJ,
    name="Maryknoll Example (POJ front)",
    fields=EXAMPLE_FIELDS,
    templates=[{
        "name": "Card",
        "qfmt": '<div class="front-big poj">{{poj}}</div>',
        "afmt": EXAMPLE_BACK,
    }],
    css=CSS,
)


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fields_for(row: dict, schema: list[dict]) -> list[str]:
    return [row.get(f["name"], "") or "" for f in schema]


def build_deck(deck_id: int, name: str, model, rows, schema, guid_prefix: str, key: str):
    deck = genanki.Deck(deck_id, name)
    for i, row in enumerate(rows):
        guid = genanki.guid_for(f'{guid_prefix}-{row[key]}-{i}')
        deck.add_note(genanki.Note(
            model=model,
            fields=fields_for(row, schema),
            guid=guid,
        ))
    return deck


def main() -> None:
    decks: list[genanki.Deck] = []

    for lesson in LESSONS:
        vocab_rows = load_csv(CSV_DIR / f"maryknoll_book1_lesson{lesson}_vocab.csv")
        ex_rows = load_csv(CSV_DIR / f"maryknoll_book1_lesson{lesson}_examples.csv")

        base = f"Maryknoll Book 1::Lesson {lesson}"

        decks.append(build_deck(
            DECK_ID_BASE + lesson * 10 + 0,
            f"{base}::Vocab (Hanji front)",
            vocab_hanji_model, vocab_rows, VOCAB_FIELDS,
            f"mk-l{lesson}-v-h", "number",
        ))
        decks.append(build_deck(
            DECK_ID_BASE + lesson * 10 + 1,
            f"{base}::Vocab (POJ front)",
            vocab_poj_model, vocab_rows, VOCAB_FIELDS,
            f"mk-l{lesson}-v-p", "number",
        ))
        decks.append(build_deck(
            DECK_ID_BASE + lesson * 10 + 2,
            f"{base}::Examples (Hanji front)",
            example_hanji_model, ex_rows, EXAMPLE_FIELDS,
            f"mk-l{lesson}-e-h", "vocab_number",
        ))
        decks.append(build_deck(
            DECK_ID_BASE + lesson * 10 + 3,
            f"{base}::Examples (POJ front)",
            example_poj_model, ex_rows, EXAMPLE_FIELDS,
            f"mk-l{lesson}-e-p", "vocab_number",
        ))

    genanki.Package(decks).write_to_file(OUT_FILE)
    total_notes = sum(len(d.notes) for d in decks)
    print(f"Wrote {OUT_FILE}")
    print(f"  {len(decks)} decks, {total_notes} notes total")


if __name__ == "__main__":
    main()
