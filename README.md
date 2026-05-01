# Taiwanese (Hokkien) Anki Decks

This is a curated collection of Taiwanese Language (Tâi-gí / Hokkien) Anki decks
that I have generated from various sources. I used Claude to extract the vocabulary
and example sentences from PDFs of the books, then I edited the transcription errors manually.
There may still may be errors in transcription, tone change and use of Hàn-jī.

Current collection:
- [Maryknoll Taiwanese Book 1 with Hàn-jī on the front](maryknoll-book-1/decks/maryknoll_book1_all_hanji_front.apkg)
- [Maryknoll Taiwanese Book 1 with Pe̍h-ōe-jī on the front](maryknoll-book-1/decks/maryknoll_book1_all_poj_front.apkg)

## How to generate the decks from the CSVs

First-time setup:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Build:

```bash
.venv/bin/python build.py
```

## Editing the CSVs

Per lesson data lives in `maryknoll-book-1/csv/`:

- `maryknoll_book1_lesson{N}_vocab.csv` are collections of vocabulary words per lesson.
- `maryknoll_book1_lesson{N}_vocab_examples.csv` are collections of vocabulary example sentences per lesson.

After editing, rerun `build.py` and the `.apkg` files will update in place.

See `CLAUDE.md` for the project's conventions on Pe̍h-ōe-jī normalization, tone
sandhi rules, and recommended Taiwanese Hàn-jī forms. 

## Attribution

Vocabulary, example sentences, and lesson structure are adapted from
Maryknoll Taiwanese Book 1, published by the Maryknoll Language Service
Center, Taichung, Taiwan. The Anki formatting, sandhi numbering scheme, and
build pipeline in this repository are original work, and may be reused under 
the license conditions.

Taiwanese Hàn-jī were collected from the [MOE Taiwanese Dictionary 教育部臺灣台語常用詞辭典](https://sutian.moe.edu.tw/zh-hant/).

Pe̍h-ōe-jī and tone sandhi rules are based on the information found in the 
Maryknoll Taiwanese Books. They represent the Taichung accent at the time of 
publishing.

## License

This project is released under the **Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International** license
([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)).

Maryknoll's source dictionary materials were released under CC BY-NC-SA
3.0; CC BY-NC-SA 4.0 is a ShareAlike-compatible upgrade. You may
use, adapt, and redistribute these decks freely for non-commercial purposes
provided you (a) credit Maryknoll Language Service Center as the source and
(b) license your derivative work under the same terms. See `LICENSE` for
the full notice.
