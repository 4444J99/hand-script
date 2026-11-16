# hand-script

**Scope.** The owner's handwriting practice and learning of new writing systems and scripts:
practice material, stroke and letterform notes, and etymology of the scripts being learned.
It is not Chaucer or Middle English scansion (that is `4444J99/chaucer`, which was this
repository's name until 2026-11-15) and not vers.forms, the owner's poetry studio
(`4444J99/journal-handwritten-web`, `4444J99/versforms`). Private.

Origin: the Perplexity Space `053d129c-8941-4aa7-8dde-61aede81813d` began as a
handwriting-practice and linguistics curriculum (writing systems, etymological roots, 18
languages in nine families). Its Middle English turn of 2026-11-10 moved to `chaucer`.

Plan: `.claude/plans/2026-11-16-handwriting-practice-and-tracker.md`.

## Use

```bash
PYTHONPATH=src python3 -m hand_script sheets all --out sheets
```

Writes printable HTML (open in a browser, print A4): a letter sheet and a line-copy sheet
per script (Greek, Hebrew so far). New script = new JSON file in `src/hand_script/data/`.

Practice log (append-only `data/practice-log.jsonl`, or `--file` / `$HAND_SCRIPT_LOG`):

```bash
PYTHONPATH=src python3 -m hand_script log add greek --minutes 10 --lines 3 --characters 45 --focus "α β γ"
PYTHONPATH=src python3 -m hand_script log summary
```

Tests: `PYTHONPATH=src python3 -m unittest discover -s tests`.
