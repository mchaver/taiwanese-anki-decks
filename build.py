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
import shutil
import zipfile
from pathlib import Path

import genanki

# Fixed build timestamp — makes .apkg output reproducible so identical CSVs
# produce byte-identical files. Without this, every rebuild rewrites note/card
# mod times and zip entry mtimes, polluting git diffs.
BUILD_TIMESTAMP = 1577836800.0  # 2020-01-01 UTC
ZIP_MTIME = (2020, 1, 1, 0, 0, 0)

ROOT = Path(__file__).parent
BOOK_DIR = ROOT / "maryknoll-book-1"
CSV_DIR = BOOK_DIR / "csv"
OUT_DIR = BOOK_DIR / "decks"

LESSONS = [1, 2, 3, 4, 5, 6, 7, 8]

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


def normalize_zip_mtime(path: Path) -> None:
    """Rewrite all zip entries with a fixed mtime so the .apkg is reproducible."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            info.date_time = ZIP_MTIME
            zout.writestr(info, zin.read(info.filename))
    shutil.move(tmp, path)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    variants = [
        # (kind, model, schema, filename_suffix, deck_name_suffix, guid_prefix, key)
        ("vocab",   vocab_hanji_model,   VOCAB_FIELDS,   "vocab_hanji_front",    "Vocab (Hàn-jī)",       "v-h", "number"),
        ("vocab",   vocab_poj_model,     VOCAB_FIELDS,   "vocab_poj_front",      "Vocab (Pe̍h-ōe-jī)",    "v-p", "number"),
        ("example", example_hanji_model, EXAMPLE_FIELDS, "examples_hanji_front", "Examples (Hàn-jī)",    "e-h", "vocab_number"),
        ("example", example_poj_model,   EXAMPLE_FIELDS, "examples_poj_front",   "Examples (Pe̍h-ōe-jī)", "e-p", "vocab_number"),
    ]

    total_notes = 0
    total_files = 0

    for lesson in LESSONS:
        vocab_rows = load_csv(CSV_DIR / f"maryknoll_book1_lesson{lesson}_vocab.csv")
        ex_rows = load_csv(CSV_DIR / f"maryknoll_book1_lesson{lesson}_examples.csv")
        rows_by_kind = {"vocab": vocab_rows, "example": ex_rows}

        base = f"Maryknoll Book 1 - Lesson {lesson}"

        for idx, (kind, model, schema, file_suffix, deck_suffix, prefix, key) in enumerate(variants):
            deck = build_deck(
                DECK_ID_BASE + lesson * 10 + idx,
                f"{base} - {deck_suffix}",
                model, rows_by_kind[kind], schema,
                f"mk-l{lesson}-{prefix}", key,
            )
            out_path = OUT_DIR / f"maryknoll_book1_lesson{lesson}_{file_suffix}.apkg"
            genanki.Package([deck]).write_to_file(out_path, timestamp=BUILD_TIMESTAMP)
            normalize_zip_mtime(out_path)
            print(f"  {out_path.name} ({len(deck.notes)} notes)")
            total_notes += len(deck.notes)
            total_files += 1

    print(f"\nWrote {total_files} .apkg files to {OUT_DIR}/")
    print(f"  {total_notes} notes total")


if __name__ == "__main__":
    main()
