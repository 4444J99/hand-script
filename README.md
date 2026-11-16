# hand-script

**Scope.** The owner's handwriting practice and learning of new writing systems and scripts:
practice material, stroke and letterform notes, and etymology of the scripts being learned.
It is not Chaucer or Middle English scansion (that is `4444J99/chaucer`, which was this
repository's name until 2026-11-15) and not vers.forms, the owner's poetry studio
(`4444J99/journal-handwritten-web`, `4444J99/versforms`). Private.

Origin: the Perplexity Space `053d129c-8941-4aa7-8dde-61aede81813d` began as a
handwriting-practice and linguistics curriculum (writing systems, etymological roots, 18
languages in nine families). Its Middle English turn of 2026-11-10 moved to `chaucer`.

## Overview

`hand-script` is a pure-stdlib Python (`>=3.11`) workbench that turns the surviving
Perplexity Space and imported ChatGPT archive into inspectable JSON registries, validators,
and deterministic printable A4 HTML handwriting sheets.

### Repository Layout

- `docs/perplexity/` — Verbatim preserved Space artifacts (`HS-M001-project-manifest.md`, `HS-M001-inventory.json`, `HS-F001-F002-preservation-report.md`) and `PROVENANCE.md` with verified SHA-256 digests.
- `src/hand_script/data/` — Five structured JSON registries:
  - `project_manifest.json` (`hand-script.manifest/1`): 12 native Perplexity threads, 3 imported ChatGPT exports, 3 SHA-256-verified repo documents, 3 audited unrecovered claims, and component status parity.
  - `scripts.json` (`hand-script.scripts/1`): 14 writing systems typed under Daniels & Bright (1996) (`alphabet`, `abjad`, `abugida`, `syllabary`, `morphographic`, `featural`), 4 ruling geometries (`four-line`, `abjad-rtl`, `head-line`, `square-grid`), ductus notes, exemplar glyphs, and 3 coexisting sequencing tracks (`kanji-first-stack`, `greek-first-protocol`, `typological-distance`).
  - `languages.json` (`hand-script.languages/1`): Comparative language and founding-text pathways across 9+ language families, separating Homeric vs Koine/Septuagint Greek and Classical Augustan vs Vulgate Latin, with an explicit boundary pointer to `4444J99/chaucer` for Middle English scansion.
  - `lexical_network.json` (`hand-script.lexical-network/1`): 5 concept clusters, 30 relationship-labeled edges (`cognate`, `word_formation`, `borrowing`, `translation`, `interpretation`, `comparison`), and 8 canonical opening passages for handwriting copying.
  - `linguistics_canon.json` (`hand-script.linguistics-canon/1`): 28 recurring foundational works staged across `undergraduate`, `graduate`, and `doctoral` study and 11 subfields.
- `src/hand_script/` — Core library and `hand-script` CLI:
  - `manifest.py`: Schema, UUID, and SHA-256 provenance verifier.
  - `scripts.py`: Writing-system catalog and `check_interference` analyzer (flags concurrent lookalike bicameral scripts, concurrent initial RTL abjads, and concurrency-cap overruns while marking numerical thresholds heuristic).
  - `unicode_inspect.py`: Pure-stdlib `unicodedata` grapheme cluster and combining-mark inspector (Greek polytonic diacritics, Hebrew niqqud, Arabic harakat, Devanagari matras/virama).
  - `curriculum.py`: Comparative language map and staged linguistics meta-canon queries.
  - `etymology.py`: Typed lexical network validator that rejects cross-family `cognate` edges and cross-language `word_formation` edges.
  - `notebook.py`: Deterministic 6-step Notebook Practice Protocol planner (`warm_up`, `copying`, `memory_rewrite`, `observation`, `composition`, `reflection`), 6 observable milestones, and JSONL session-log validator.
  - `renderings.py`: Version-bound orthogonal script rendering validator (`hand-script.rendering/1`) enforcing `source_sha256` staleness detection, `reserve` pool export blocks, native-reader review requirements, and separated author/collaborator/public permission gates.
  - `practice.py`: Deterministic A4 HTML exemplar glyph sheets and multi-script passage practice sheets with inline SVG rulings (`four-line`, right-aligned `abjad-rtl`, Shirorekha `head-line`, and Tianzige `square-grid`).
  - `atlas.py`: Self-contained HTML comparative script, root, and canon atlas.
- `sheets/` — Committed byte-deterministic HTML deliverables (`greek_alphabet.glyph.html`, `kanji_radicals.glyph.html`, `arabic_abjad.glyph.html`, `devanagari_abugida.glyph.html`, `opening_passages.practice.html`, `hand_script_atlas.html`).
- `tests/` — 19 `pytest` suites covering schema validation, SHA-256 provenance, cross-family cognate rejection, rendering gates, SVG geometry, sheet determinism, and CLI subcommands.

## Archive Audits & Design Guardrails

1. **Count audit (`HS-T005` Turn 6):** Turn 6 headlines "18 Languages across 9 Major Families", while its itemized breakdown names 16 languages (`6 + 2 + 2 + 1 + 1 + 1 + 1 + 1 + 1`). `languages.json` marks those 16 entries `turn6-core` and records `korean` and `geez` (from `HS-T005` Turns 4–5 and `HS-F013`) as `archive-expansion` so both totals (`16` and `18`) are exact and auditable.
2. **Etymology correction (`*ped-` vs `нога`):** `HS-T005` Turn 3 erroneously derived Russian `нога` ("foot/leg") from PIE `*ped-`. `lexical_network.json` records `пеший` ("on foot") as the inherited Slavic `*ped-` cognate and links `нога` (from Proto-Slavic `*noga`, "claw/hoof") via `comparison`.
3. **Cognate vs translation discipline:** Cross-family links cannot be labeled `cognate`. Semitic `שָׁלוֹם` and `سَلَام` share root `*š-l-m` (`cognate`), whereas Septuagint `εἰρήνη` / `σωτηρία` and Vulgate `pāx` are modeled as passage-anchored `translation` edges.
4. **Coexisting sequencing tracks:** Neither the owner's 4-layer `kanji-first-stack` (`HS-T009` Turns 5–6) nor the `greek-first-protocol` (`HS-F001`) is erased; both are first-class tracks in `scripts.json`.
5. **Unexported upstream claims:** The claimed 4,000-reference attachment in `HS-T002` and the eight starter Markdown files claimed in `HS-T005` were never exported into the Perplexity Space and are documented under `unrecovered_claims` in `project_manifest.json`.

## Quickstart

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

# Verify manifest and SHA-256 digests of preserved Space files
.venv/bin/hand-script manifest --repo-root .

# List writing systems or inspect a sequencing track
.venv/bin/hand-script scripts
.venv/bin/hand-script scripts --track kanji-first-stack

# Check concurrent script selections for interference
.venv/bin/hand-script check-interference greek cyrillic
.venv/bin/hand-script check-interference hebrew arabic

# Inspect Unicode codepoints and combining marks
.venv/bin/hand-script inspect-text "Μῆνιν שָׁלוֹם पद्" --skip-whitespace

# Query comparative languages, lexical clusters, and linguistics canon
.venv/bin/hand-script languages --status turn6-core
.venv/bin/hand-script network --cluster peace-wholeness
.venv/bin/hand-script canon --subfield writing_systems

# Plan a 20-minute 6-step notebook practice session
.venv/bin/hand-script plan-session arabic --minutes 20 --passage FATIHA.1.1

# Regenerate printable A4 HTML sheets and comparative atlas
.venv/bin/hand-script glyph-sheet greek -o sheets/greek_alphabet.glyph.html
.venv/bin/hand-script glyph-sheet kanji -o sheets/kanji_radicals.glyph.html
.venv/bin/hand-script glyph-sheet arabic -o sheets/arabic_abjad.glyph.html
.venv/bin/hand-script glyph-sheet devanagari -o sheets/devanagari_abugida.glyph.html
.venv/bin/hand-script practice-sheet -o sheets/opening_passages.practice.html
.venv/bin/hand-script render-atlas -o sheets/hand_script_atlas.html
```

## Verification

Verified locally across Python `3.11.17`, `3.12.15`, and `3.13.16` (`ruff check .`,
`ruff format --check .`, and `pytest` — 19 passed in ~0.2s per interpreter). Note that
hosted GitHub Actions runners on private repositories under `4444J99` require billing/runner
entitlement to start jobs; `.github/workflows/ci.yml` mirrors the exact local `3.11` /
`3.12` / `3.13` verification matrix.
