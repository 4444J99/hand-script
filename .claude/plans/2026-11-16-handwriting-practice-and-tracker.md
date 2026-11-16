# Plan: handwriting practice sheets and practice tracker

Status: slice 1 (sheets) shipped in PR 2; slice 2 (log CLI: `log add`, `log summary` with streaks) shipped in the follow-up PR. Project scope: handwriting and learning new
scripts only. Not Chaucer (`4444J99/chaucer`), not vers.forms.

## Evidence (owner's own words, ChatGPT conversations in the knowledge library)

- "Classical Music for Iliad" (chatgpt-6a394740): "i would like to accompany my
  reading w education, learning new scripts/language by handwriting & translating".
  The assistant's reply the owner built on set the shape: *script first, grammar
  second, translation third*; "the key is not fluency, the key is physical contact
  with the text"; a daily minimum of **10 minutes handwriting 3-5 lines**, and a
  per-day ledger.
- "Daily Improvement Routine" (chatgpt-6a4c46f7): owner wants "learning new scripts
  and characters" daily, with morning/evening check-in so "we can start tracking
  statistics and data"; the suggested metric for scripts is *minutes or characters
  practiced*.

## Which scripts (the owner's order)

1 Greek, 2 Latin, 3 Italian (Latin script, so only diacritics/hand style),
4 Hebrew, 5 Arabic, 6 Old English (insular letters), 7 Devanagari, 8 Hanzi,
9 Kana, 10 Persian. Slices 1-2 ship **Greek** and **Hebrew** (alphabet data in
`src/hand_script/data/`); the format is data-driven so each further script is a
data file, not code.

## Which practice materials

Printable, self-contained HTML (print to A4/Letter; no network, no fonts to
install beyond system fonts). Per script:
1. **Letter sheet**: one row per letter, ghost (light) models then blank guided
   cells, with name, transliteration, sound. Baseline/x-height/ascender guides.
2. **Line-copy sheet**: guided ruled lines with a model line to copy by hand
   (3-5 lines a day, per the owner's daily minimum).
Texts for line copying are public-domain opening lines in the original script
(Greek: Iliad 1.1 opening, Hebrew: Genesis 1:1), matching the owner's reading list.

## How progress is tracked

Append-only JSONL log at `data/practice-log.jsonl` (git-tracked, local only, no
app stores). One entry per sitting: date, script, minutes, characters/lines,
focus letters, note. `hand-script log add|summary` (streaks are part of the summary). Summary reports minutes,
characters, sitting days, current/longest streak, and per-script totals. Mirrors
the owner's "minutes or characters practiced" metric and the 10-minute daily minimum.

## Slices

1. Plan + data-driven sheet generator + Greek and Hebrew letter/copy sheets.
2. Practice log CLI with summaries and streaks.

Out of scope for now: translation workflow, audio, OCR/feedback on scans.
