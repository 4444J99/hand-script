# Perplexity Project Provenance

Source Perplexity Space: `hand-script` (`053d129c-8941-4aa7-8dde-61aede81813d`)
Retrieved: `2026-11-15`

## Imported Verbatim in `docs/perplexity/`

| Path | Manifest ID | SHA-256 | Notes |
|---|---|---|---|
| `docs/perplexity/HS-M001-project-manifest.md` | `HS-M001` | `01fbf635bf874cff4918849cd87a28b61e67f01cc6e52f1d8cc5e15da1614634` | Annotated manifest v0.3 (2026-11-09) cataloging exports, PDFs, and preservation reports |
| `docs/perplexity/HS-M001-inventory.json` | `HS-M001` | `14a277acdb60a2d2a80b3a288ae83a80e5b072f6ac92858740dfa1c69f193884` | Structured inventory for `HS-M001` v0.3 |
| `docs/perplexity/HS-F001-F002-preservation-report.md` | `HS-A003` | `aa97c2846bb92a6368ed34eaa6d293e16bc8a8d174992669929ecd5465f1f5a0` | Extracted text and MD5 comparison of `010426-unique_scripts-notebook-practice_v1.pdf` and `_v2.pdf` (identical text) |

## Indexed in `src/hand_script/data/project_manifest.json` (Retained in Space Checkout)

The remaining exports and turn-by-turn preservation reports remain in the Perplexity Project file repository (`hand-script-BT0SnIlBSqeN3mGu3oGBPQ/files`) rather than duplicating ~600 KB of raw chat transcripts in Git. Their SHA-256 digests at retrieval time (`2026-11-15`) are recorded below and validated by `hand-script manifest --check`:

| Space Path | Manifest ID | Native Thread UUID | SHA-256 |
|---|---|---|---|
| `HS-M001-inventory.csv` | `HS-M001` | `e6f00320-1b27-4632-b192-39603e8c97cc` | `5bf656eceb7c66ffa0a5d69c714746e298b392044d33aeb333ddc558636a6290` |
| `Writing the World's Scripts Through 100 Poems_ Learning Roadmap, Rendering Modes and Rights Cautions.md` | `HS-F013` | `3377c206-3254-470b-8ac6-261610f98aa9` | `e094262cc934148a1654cc689792f5dc21a3dacf3e182553cfb0f0efc463cafa` |
| `preservation/HS-T001-preservation-report.md` | `HS-A004` | `8731a6a7-2f3c-4faf-957c-48f14c3792ce` | `1945c68214cc5e6e404dfaa950ef5a424d0dde9e6e4c8cb46d9b2209089c2fa6` |
| `preservation/HS-T002-preservation-report.md` | `HS-A005` | `0a7dad6d-8f2f-4c64-8b80-6279521a4194` | `2de4fa3ab533abb2c8144e960e216988b5836b459aac224ae6422d85e6153a4f` |
| `preservation/HS-T003-preservation-report.md` | `HS-A006` | `021ebcdc-1d87-4e2d-a339-e4d4e70ecc2a` | `3e42207775a11010c90601e3f59597d0ac3ba103f74b40e79118db3f7c7db363` |
| `preservation/HS-T004-preservation-report.md` | `HS-A007` | `2b738e12-f550-46e3-b1ce-8466bd70644b` | `35feb5915a42965911e2a48b00adc867651e122343646874c74fde3e11608edc` |
| `preservation/HS-T005-preservation-report.md` | `HS-A008` | `4826f815-927a-41d6-9311-15a903f09d3f` | `c2de710936b0267f56b7b344d2e5d25bbd2ba5d1dabd4885391e3c0a480631b1` |
| `preservation/HS-T006-preservation-report.md` | `HS-A009` | `5e65736a-3dc6-4889-b78b-b741a0813280` | `cd16cde0895295ac2e5ee5a993a07d0d7d8dc4c6ad56f04d220c8908ca38b538` |
| `preservation/HS-T007-preservation-report.md` | `HS-A010` | `3b98b8a1-6241-4e0f-a7d8-877a2187cd0e` | `7c7654ff6239897e68c44e1e1a8d0791a98e8568e17d4d04c9292697678f766d` |
| `preservation/HS-T009-preservation-report.md` | `HS-A011` | *(ChatGPT export)* | `a5123ac42650a76094c9d8c5752ca4cebefeda89e07568701337871ef0754795` |
| `preservation/HS-T010-preservation-report.md` | `HS-A012` | *(ChatGPT branch)* | `7550b09d26dc18b04e5c3a8ffd0d7f9495e66beba6a25323ba9cda05aeed5e10` |
| `preservation/HS-T011-preservation-report.md` | `HS-A013` | *(ChatGPT export, off-topic)* | `abb234bbe0ffe494058d4cbb0f32e94d6288c9e1ffbbc65d52b5af7931686dc1` |

## Repository Boundary Note

Until `2026-11-15`, the repository now at `4444J99/chaucer` carried the name `hand-script`. On `2026-11-15`, the Middle English scansion and *Canterbury Tales* work stayed in `4444J99/chaucer`, while this repository (`4444J99/hand-script`) was initialized exclusively for handwriting practice, writing-system typology, stroke/letterform study, relationship-labeled lexical study, and script-learning sheets. Editorial publication and handwritten journal pieces remain in `4444J99/journal-handwritten-web` and `4444J99/versforms`.
