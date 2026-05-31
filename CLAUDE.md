# Maryknoll Taiwanese → Anki Decks

This project turns vocabulary and example sentences from the Maryknoll Taiwanese textbooks into Anki decks.

## Layout

- `build.py` — deterministic genanki build script at repo root
- `maryknoll-book-{N}/csv/` — hand-curated source CSVs (vocab + examples, one pair per lesson)
- `maryknoll-book-{N}/decks/` — generated `.apkg` files (committed; deterministic builds mean diffs only reflect content changes)
- `/Users/mchaver/Documents/books/taiwanese/Maryknoll_Taiwanese_Book_{N}.pdf` — the source textbooks

## Extracting a new lesson

Use the **`extract-lesson` skill** (`.claude/skills/extract-lesson/`) — it has the full PDF→CSV workflow (rendering pages, transcribing POJ + tone-sandhi numbers from the scanned images, delegating page transcription to subagents to dodge the image-context cap, writing the two CSVs, and building). In brief: render pages → transcribe → write `maryknoll_book{N}_lesson{M}_vocab.csv` + `..._vocab_examples.csv` → add the lesson to `LESSONS` in `build.py` → `.venv/bin/python build.py` and verify row counts.

## CSV schemas

### Vocab

`number, poj, poj_sandhi, taiwanese_hanji, mandarin, english, notes`

One row per headword. The `notes` column holds parenthetical explanations, grammar cross-references, and literal meanings — not the core gloss.

### Examples

`vocab_number, poj, poj_sandhi, taiwanese_hanji, english`

Normalized — one row per example sentence, `vocab_number` is a foreign key to the vocab CSV. A vocab entry can have 0 or many examples.

The examples file holds **only full example sentences**. Do not put bare vocabulary words here.

### Sub-headwords (words listed under a main entry)

Under a numbered main headword the book often lists **derived words / sub-headwords** — these are real vocabulary, not example sentences. Examples: `a-só` under `a-hiaⁿ`; the son/daughter terms (`cha-po·-kiáⁿ`, `hāu-seⁿ`, …) under `kiáⁿ`; the literary number readings under the `it/jī/…` entry; verb-object collocations the book sets as sub-entries (`chò kang`, `khui kang-tiûⁿ`, `kóng kò·-sū`). The distinction: a sub-headword is a word/phrase with a gloss; an example is a full sentence with a translation.

Handle them as follows:

- **Each sub-headword becomes its own row in the *vocab* file**, inserted immediately **after its parent**, then the whole list is **renumbered sequentially** in book order. (Give it a `mandarin` gloss and move any parenthetical from the gloss into `notes`, like any vocab entry.)
- **Example sentences stay in the examples file**, with their `vocab_number` re-pointed to the parent's new number (sentences keep illustrating the main headword).
- After renumbering, validate: every `vocab_number` in examples must exist in vocab (no orphan foreign keys), and `build.py` row counts should match expectations.

### CSV quoting

Standard RFC 4180. Any field containing `,`, `"`, or newlines **must** be quoted, with internal `"` doubled. Forgetting this silently corrupts rows — `csv.DictReader` fills in `None` keys and the build proceeds with bad data. When the build reports fewer rows than the user expects, look for malformed quoting.

## POJ conventions

- **Nasalization:** `ⁿ` (U+207F), never `*`. Example: `chîⁿ`, not `chî*`.
- **Dot-above-right tone:** `·` (interpunct). Example: `kho·`, `bô·`.
- **Tone 8 marker:** `̍` (combining vertical line, U+030D). Example: `chia̍h`, `tha̍k`, `Bo̍k`.
- **Normalized spellings** (may differ from some older book spellings):
  - `boeh` (not `bóeh`) — "to want / future"
  - `siá` (not `sia`) — "to write"
  - `chia̍h` (not `chiah`) — "to eat"
  - `mi̍h-kiāⁿ` (not `mîⁿ-kiāⁿ`) — "thing"
  - `toh-ūi` / `tah-ūi` (not `tó·-ūi`) — "where"
  - `lo̍h` (tone 8, not `loh` tone 4) — "down" (e.g., `lo̍h-chhia`, `lo̍h-lâi`)
  - `niā-niā` (tone 7, not `niâ-niâ` tone 5) — "only"
  - `chin` (tone 1, no diacritic — not `chīn` tone 7) — "very"; sandhi `chin7-` (tone 1 → 7), not `chīn3-`
  - Sentence-final perfect-tense particle `a` is written **without diacritic** (tone 1 base), distinct from the diminutive suffix `-á` (always hyphenated). See rule 13.

## Tone sandhi

Sandhi numbers are appended after each non-final syllable of a tone group, indicating the syllable's target tone in context. The **final** syllable carries no number (same as base POJ).

Examples: `Gâu7-chá`, `lōa3-chē`, `Che ài2 lōa3-chē`.

### Substitution table (non-final position)

| Base tone | Becomes |
|---|---|
| 1 (no mark, `a`) | 7 |
| 2 (acute, `á`) | 1 |
| 3 (grave, `à`) | 2 |
| 5 (circumflex, `â`) | 7 |
| 7 (macron, `ā`) | 3 |
| 4 (no mark + `-p/-t/-k/-h`) | 2 |
| 8 (vertical bar + `-p/-t/-k/-h`) | 3 |

### Exceptions (judgment calls, applied pragmatically)

1. **Single-character nouns** usually do **not** change tone (e.g., `chhù`, `chheh`, `mn̂g` stay at base tone even in non-final position).
2. **The last character of a noun / noun phrase** usually does not change tone.
3. **Demonstrative pronouns** (`che`, `he`, `chia`, `hia`) do not change tone. (Note: `chit`/`hit` are demonstrative *modifiers* — they sandhi normally as tone 4 → 2.)
4. **Enclitics sit outside the tone group (the "1-3-7 rule").** A clause-final enclitic — question particles `bô·?`/`bē?`/`bōe?`/`lè?`, perfect `a`, nominalizer `ê`, directional `lâi`/`khì`, a sentence-final pronoun, the "see" complements `-tio̍h`/`-kìⁿ`, the double enclitic `-chit-ē` — does **not** make the word it attaches to sandhi: that host word behaves as phrase-final and stays at **base** tone. The enclitic's **own** tone follows the **1-3-7 rule**: it sits at **tone 3**, but surfaces as **tone 7** when the syllable it attaches to carries **tone 7 in context** (base or sandhied). Examples → 7: `hō ê7`, `bô7-tī-lē a7`, `kúi nî-ê7`; → 3 (default): `bé-ê3`, `kú a3`, `chia̍h-khì ê3`, `kóng-chit3-ē3`, `tán-chit3-ē3`. Per-enclitic specifics: directional `lâi` → `lâi3` (e.g. after `tńg`/`khit`/`lo̍h`/`peh-` — `tō3 tńg-lâi3`); directional `khì` and `-kìⁿ` stay base (their base is already tone 3 — `chhut-khì`, `khòaⁿ-kìⁿ`); `-tio̍h` → `tio̍h3` (`khòaⁿ-tio̍h3`); question particles `bô·`/`bē`/`bōe` are fixed at tone 3 (`bô·3?`, `bē3?`). **If material follows the enclitic**, the host is no longer phrase-final and sandhis normally: `khòaⁿ2-tio̍h3 góa...` (vs clause-final `khòaⁿ-tio̍h3`), `ē3-ēng3-tit2 khiâ ...` (vs clause-final `ē3-ēng-tit3`). When in doubt, defer to the book's printed numbers.
5. **Proper nouns / surnames** (e.g., `Tân`, `N̂g`) often don't sandhi.
6. **Comma and semicolon** break the tone group: the syllable before the punctuation stays at its base tone.
7. **Diminutive suffix `-á`** stays at its base tone and does not sandhi, even in non-final positions (e.g., `í1-á-kha`, `toh2-á-téng`, `chím1-á teh2 tha̍k3-chheh`).
8. **Tone 7 or 8 noun + `-á` suffix**: the noun itself also stays at its base tone (the whole word is "frozen"). Example: `chhiū-á` (tree) stays as `chhiū-á`, never `chhiū3-á`.
9. **`Sian-siⁿ`** (先生) is irregular and depends on context:
   - **Alone as a noun** (no surname directly before, e.g., `Lín sian-siⁿ`, `sím-mih sian-siⁿ`): tones are **7-1** → `sian7-siⁿ`.
   - **Preceded by a surname** (e.g., `Tân Sian-siⁿ`, `Khó· Sian-siⁿ`, `Tē Sian-siⁿ`): the **surname does not change tone** and Sian-siⁿ becomes **3-3** → `Tân Sian3-siⁿ3`, `Khó· Sian3-siⁿ3`, `Tē Sian3-siⁿ3`.
10. **`ē-hiáu` questions pair with `bē`** (not `bô·`). The form is `... ē-hiáu ... bē?` (會...袂?), not `... ē-hiáu ... bô·?`. `bē` at the end of such a question takes sandhi tone 3 (`bē3`), and (like `bô·3`) it does not trigger sandhi on the preceding word. Example: `Lí ē-hiáu khòaⁿ sî-cheng bē?` → `Lí1 ē3-hiáu1 khòaⁿ2 sî7-cheng bē3?`
11. **`iōng + Verb + ê` construction** ("by means of"): the verb does **not** sandhi, and the trailing `ê` follows the 1-3-7 rule (rule 4). Examples: `iōng3-kiâⁿ-ê7 lâi` (`kiâⁿ` carries tone 7 in context → `ê7`), `iōng3-siá-ê3` (`siá` is tone 2 → `ê3`).
12. **Verb + pronoun at sentence end**: when a sentence ends with a verb (or verb compound) immediately followed by a pronoun, the **last syllable of the verb does not change tone**, and the **pronoun shifts per the 1-3-7 rule** (in practice landing on tone 3 — e.g., `i` tone 1 → `i3`, `góa` tone 2 → `góa3`). Example: `Góa m̄-bat i.` → `Góa1 m̄3-bat i3.`
13. **Sentence-final perfect-tense particle `a`** (矣) is base tone 1 and is written without a diacritic to distinguish it from the diminutive suffix `-á` (which is hyphenated). It follows the 1-3-7 rule (rule 4): tone 3 by default, tone 7 after a tone-7 host. The preceding word is unaffected (it is the last content word of the clause, so it stays at its base tone). Examples: `Góa chia̍h pá a.` → `Góa1 chia̍h3 pá a3.`; `chím-á bô a.` → `chím1-á bô a3.`; `Goán pa-pah bô-tī-lē a.` → `goán1 pa-pah bô7-tī-lē a7` (host `lē` is tone 7 → `a7`).

14. **Potential / resultative complement `V-ē/bē-X`** ("can / can't manage to …") is one tone group: the verb sandhis, `ē`/`bē` → tone 3, and the **final** complement stays at base. Examples: `kóng1-bē3-thong`, `phah2-bē3-thong`, `chia̍h3 ē3 liáu1 bē3`.

When in doubt, defer to explicit tone numbers above syllables on the book page.

## Taiwanese Hanji

Use Taiwan Ministry of Education (MOE) 臺灣閩南語漢字 recommended forms. Some of the important ones in this project (mostly where they differ from common Mandarin equivalents):

| POJ | Taiwanese Hanji | Mandarin |
|---|---|---|
| bô | 無 | 沒有 |
| bōe | 未 | — (perfective negation) |
| boeh | 欲 | 要 |
| che | 這 | 這個 |
| chē (many) | 濟 | 多 |
| chheh | 冊 | 書 |
| chhù | 厝 | 房子/家 |
| chia | 遮 | 這裡 |
| chia̍h | 食 | 吃 |
| chîⁿ | 錢 | 錢 |
| ê (measure) | 个 | 個 |
| ê (possessive) | 的 | 的 |
| goán | 阮 | 我們 (exclusive) |
| he | 彼 | 那個 |
| hia | 遐 | 那裡 |
| hō· (give) | 予 | 給 |
| hō·-chò / kiò-chò | 號做 / 叫做 | 叫做 |
| in | 𪜶 | 他們 |
| kah / kap | 佮 | 和 / 跟 |
| kho· | 箍 | 元/塊 |
| kóa | 寡 | 些 |
| kóng | 講 | 說 |
| kún-chúi | 滾水 | 開水 |
| lán | 咱 | 我們 (inclusive) |
| lè / teh | 咧 | 呢 / 正在 |
| lim | 啉 | 喝 |
| lín | 恁 | 你們 |
| lōa-chē | 偌濟 | 多少 |
| m̄ | 毋 | 不 |
| m̄-sī | 毋是 | 不是 |
| mi̍h-kiāⁿ | 物件 | 東西 |
| nā | 若 | 如果 |
| niá (measure) | 領 | 件 |
| -nih | 裡 | 裡 |
| saⁿ | 衫 | 衣服 |
| sian-siⁿ | 先生 | 先生 |
| siaⁿh / siaⁿ-hòe | 啥 / 啥貨 | 什麼 |
| sím-mih | 啥物 | 什麼 |
| sím-mih-lâng / siaⁿ-lâng | 啥物人 / 啥人 | 誰 |
| tha̍k | 讀 | 讀 |
| tī | 佇 | 在 |
| toh-ūi / tah-ūi | 佗位 | 哪裡 |

## Building

```bash
# first-time setup
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# build
.venv/bin/python build.py
```

Produces 4 `.apkg` files per lesson (vocab/examples × Hàn-jī front / Pe̍h-ōe-jī front).

The build is **deterministic**: `BUILD_TIMESTAMP` is pinned and zip entry mtimes are normalized, so identical CSVs produce byte-identical `.apkg` output. That means the first rebuild after pulling changes will only dirty files whose content actually changed.

## When editing CSVs

- Make sure `taiwanese_hanji` stays in sync with `poj` — if you fix a POJ typo, double-check that the Hanji still matches word-for-word.
- The `mandarin` column is a translation, not a re-spelling of the Taiwanese Hanji. They often differ (e.g., `偌濟` vs `多少`).
- After editing, run the build and check the printed row count matches expectations.
