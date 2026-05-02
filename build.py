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
BUILD_TIMESTAMP = 1777593600.0  # 2026-05-01 UTC
ZIP_MTIME = (2026, 5, 1, 0, 0, 0)

ROOT = Path(__file__).parent
BOOK_DIR = ROOT / "maryknoll-book-1"
CSV_DIR = BOOK_DIR / "csv"
OUT_DIR = BOOK_DIR / "decks"
ASSETS_DIR = ROOT / "assets"
ESSAYS_DIR = ROOT / "essays"

# Embedded font for POJ rendering. Charis SIL is SIL OFL licensed — the OFL
# is specifically designed to permit font embedding in documents like .apkg.
EMBEDDED_FONT = ASSETS_DIR / "_charis-regular.ttf"

LESSONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

MODEL_ID_VOCAB_HANJI = 1607390001
MODEL_ID_VOCAB_POJ = 1607390002
MODEL_ID_EX_HANJI = 1607390003
MODEL_ID_EX_POJ = 1607390004

DECK_ID_BASE = 2059400000
ALL_HANJI_DECK_ID = 2059499001
ALL_POJ_DECK_ID = 2059499002

ESSAYS_PARENT_DECK_ID = 2059600000
ESSAY_DECK_ID_BASE = 2059600100  # +1 per essay

# Essays — each entry produces a subdeck under "Taiwanese Essays".
# slug maps to essays/<slug>/csv/<slug>_vocab.csv (and decks output there).
ESSAYS = [
    {"slug": "khah-tah-chhia", "title": "寒流騎腳踏車"},
]

CSS = """
@font-face {
  font-family: "Charis SIL";
  src: url("_charis-regular.ttf") format("truetype");
  font-weight: normal;
  font-style: normal;
}
.card {
  font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  font-size: 22px;
  text-align: center;
  color: #222;
  background: #fafafa;
  padding: 1em;
}
.front-big { font-size: 42px; margin: 0.5em 0; }
.poj {
  font-family: "Charis SIL", "Charis SIL Compact", "Doulos SIL",
               "Gentium Plus", "Gentium", "Noto Serif",
               "Times New Roman", "Times", serif;
}
.sandhi { color: #555; font-size: 18px; }
.mandarin { color: #666; }
.english { color: #333; }
.notes {
  color: #888;
  font-size: 15px;
  font-style: italic;
  margin-top: 1em;
  text-align: center;
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
        ("example", example_hanji_model, EXAMPLE_FIELDS, "vocab_examples_hanji_front", "Vocab Examples (Hàn-jī)",    "e-h", "vocab_number"),
        ("example", example_poj_model,   EXAMPLE_FIELDS, "vocab_examples_poj_front",   "Vocab Examples (Pe̍h-ōe-jī)", "e-p", "vocab_number"),
    ]

    total_notes = 0
    total_files = 0

    # Combined "all" decks — one for Hàn-jī front, one for Pe̍h-ōe-jī front,
    # each containing every vocab and example note across all lessons.
    # These are intended for AnkiWeb submission as standalone decks.
    common_attribution = (
        "Adapted from Maryknoll Taiwanese Book 1 (Maryknoll Language Service "
        "Center, Taichung). Licensed under CC BY-NC-SA 4.0 — "
        "https://creativecommons.org/licenses/by-nc-sa/4.0/"
    )
    # Top-level parent decks (carry the description; no notes directly).
    # The per-lesson subdecks are nested under these via "::" separators,
    # which Anki preserves on import so users can disable or delete by lesson.
    all_hanji_parent = genanki.Deck(
        ALL_HANJI_DECK_ID,
        "Maryknoll Book 1 - All (Hàn-jī)",
        description=(
            "Vocabulary and example sentences from Maryknoll Taiwanese Book 1, "
            "with Taiwanese Hàn-jī (Han characters) on the front and Pe̍h-ōe-jī "
            "(POJ romanization), tone-sandhi annotations, Mandarin translation, "
            "and English gloss on the back.\n\n" + common_attribution
        ),
    )
    all_poj_parent = genanki.Deck(
        ALL_POJ_DECK_ID,
        "Maryknoll Book 1 - All (Pe̍h-ōe-jī)",
        description=(
            "Vocabulary and example sentences from Maryknoll Taiwanese Book 1, "
            "with Pe̍h-ōe-jī (POJ romanization) on the front and Taiwanese Hàn-jī "
            "(Han characters), tone-sandhi annotations, Mandarin translation, "
            "and English gloss on the back.\n\n" + common_attribution
        ),
    )

    HANJI_SUB_BASE = 2059500000
    POJ_SUB_BASE = 2059510000

    hanji_subdecks: list = []
    poj_subdecks: list = []

    for lesson in LESSONS:
        vocab_rows = load_csv(CSV_DIR / f"maryknoll_book1_lesson{lesson}_vocab.csv")
        ex_rows = load_csv(CSV_DIR / f"maryknoll_book1_lesson{lesson}_vocab_examples.csv")
        rows_by_kind = {"vocab": vocab_rows, "example": ex_rows}

        base = f"Maryknoll Book 1 - Lesson {lesson}"
        # Zero-padded for natural sort in Anki's deck browser.
        lesson_label = f"Lesson {lesson:02d}"

        # Subdecks under each combined parent. Distinct deck IDs from the
        # per-lesson .apkg decks so they coexist if both are imported.
        sub = {
            ("vocab",   "hanji"): genanki.Deck(HANJI_SUB_BASE + lesson * 10 + 0, f"Maryknoll Book 1 - All (Hàn-jī)::{lesson_label}::Vocab"),
            ("example", "hanji"): genanki.Deck(HANJI_SUB_BASE + lesson * 10 + 1, f"Maryknoll Book 1 - All (Hàn-jī)::{lesson_label}::Vocab Examples"),
            ("vocab",   "poj"):   genanki.Deck(POJ_SUB_BASE   + lesson * 10 + 0, f"Maryknoll Book 1 - All (Pe̍h-ōe-jī)::{lesson_label}::Vocab"),
            ("example", "poj"):   genanki.Deck(POJ_SUB_BASE   + lesson * 10 + 1, f"Maryknoll Book 1 - All (Pe̍h-ōe-jī)::{lesson_label}::Vocab Examples"),
        }

        for idx, (kind, model, schema, file_suffix, deck_suffix, prefix, key) in enumerate(variants):
            deck = build_deck(
                DECK_ID_BASE + lesson * 10 + idx,
                f"{base} - {deck_suffix}",
                model, rows_by_kind[kind], schema,
                f"mk-l{lesson}-{prefix}", key,
            )
            out_path = OUT_DIR / f"maryknoll_book1_lesson{lesson}_{file_suffix}.apkg"
            pkg = genanki.Package([deck])
            pkg.media_files = [str(EMBEDDED_FONT)]
            pkg.write_to_file(out_path, timestamp=BUILD_TIMESTAMP)
            normalize_zip_mtime(out_path)
            print(f"  {out_path.name} ({len(deck.notes)} notes)")
            total_notes += len(deck.notes)
            total_files += 1

            # Mirror the same notes into the appropriate combined subdeck.
            # Same GUIDs as per-lesson decks, so importing both yields no
            # duplicates.
            lang = "hanji" if "hanji" in file_suffix else "poj"
            target = sub[(kind, lang)]
            for note in deck.notes:
                target.add_note(note)

        hanji_subdecks.extend([sub[("vocab", "hanji")], sub[("example", "hanji")]])
        poj_subdecks.extend([sub[("vocab", "poj")], sub[("example", "poj")]])

    for parent, subdecks, fname in [
        (all_hanji_parent, hanji_subdecks, "maryknoll_book1_all_hanji_front.apkg"),
        (all_poj_parent,   poj_subdecks,   "maryknoll_book1_all_poj_front.apkg"),
    ]:
        out_path = OUT_DIR / fname
        pkg = genanki.Package([parent, *subdecks])
        pkg.media_files = [str(EMBEDDED_FONT)]
        pkg.write_to_file(out_path, timestamp=BUILD_TIMESTAMP)
        normalize_zip_mtime(out_path)
        note_count = sum(len(d.notes) for d in subdecks)
        print(f"  {out_path.name} ({note_count} notes across {len(subdecks)} subdecks)")
        total_files += 1

    # ---- Essay decks ----
    # Each essay produces a Hàn-jī-front vocab deck and a vocab_examples deck
    # nested under a shared "Taiwanese Essays" parent. Example sentences are
    # author-original (illustrative usage written for these decks), distinct
    # from the source essay text.
    if ESSAYS:
        essays_parent = genanki.Deck(
            ESSAYS_PARENT_DECK_ID,
            "Taiwanese Essays",
            description=(
                "Vocabulary collected from Taiwanese-language essays. Each "
                "subdeck corresponds to one essay; cards have Hàn-jī on the "
                "front and POJ, sandhi, Mandarin, and English on the back. "
                "Example sentences in the Vocab Examples sub-subdecks are "
                "original illustrative usage, not extracts from the source "
                "essays."
            ),
        )
        for idx, essay in enumerate(ESSAYS):
            slug = essay["slug"]
            title = essay["title"]
            essay_dir = ESSAYS_DIR / slug
            essay_csv_dir = essay_dir / "csv"
            essay_decks_dir = essay_dir / "decks"
            essay_decks_dir.mkdir(parents=True, exist_ok=True)

            vocab_rows = load_csv(essay_csv_dir / f"{slug}_vocab.csv")
            vocab_deck = build_deck(
                ESSAY_DECK_ID_BASE + idx * 2,
                f"Taiwanese Essays::{title}::Vocab",
                vocab_hanji_model, vocab_rows, VOCAB_FIELDS,
                f"essay-{slug}-v-h", "number",
            )

            ex_csv = essay_csv_dir / f"{slug}_vocab_examples.csv"
            sub_decks = [vocab_deck]
            if ex_csv.exists():
                ex_rows = load_csv(ex_csv)
                ex_deck = build_deck(
                    ESSAY_DECK_ID_BASE + idx * 2 + 1,
                    f"Taiwanese Essays::{title}::Vocab Examples",
                    example_hanji_model, ex_rows, EXAMPLE_FIELDS,
                    f"essay-{slug}-e-h", "vocab_number",
                )
                sub_decks.append(ex_deck)

            out_path = essay_decks_dir / f"{slug}_hanji_front.apkg"
            pkg = genanki.Package([essays_parent, *sub_decks])
            pkg.media_files = [str(EMBEDDED_FONT)]
            pkg.write_to_file(out_path, timestamp=BUILD_TIMESTAMP)
            normalize_zip_mtime(out_path)
            note_count = sum(len(d.notes) for d in sub_decks)
            print(f"  {out_path.relative_to(ROOT)} ({note_count} notes across {len(sub_decks)} subdecks)")
            total_notes += note_count
            total_files += 1

    print(f"\nWrote {total_files} .apkg files")
    print(f"  {total_notes} notes total (combined decks share these notes)")


if __name__ == "__main__":
    main()
