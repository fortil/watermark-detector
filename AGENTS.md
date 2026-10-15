# AGENTS.md

Instructions for coding agents working in this repository. What the tool does is in `README.md`. How to use it is in `docs/43.03-guide/usage-guide.md`.

## Project

The CLI is `wmd` (alias `watermark-detector`). The package is `watermark_detector`. The tool detects AI provenance signals in files: C2PA manifests, IPTC XMP AI markers, China's GB 45438 label, and opt-in remote text verifiers for Claude, Gemini, GPT and Z.AI.

This project detects only. Never add code that removes, strips, forges or hides a mark. `tests/test_readme.py` fails if the README mentions `wmd remove`.

Python 3.11 or later is required. The development venv uses Python 3.12. Runtime dependencies are `c2pa-python==0.38.0` (exact pin) and `pypdf>=6.20,<7`. Dev extras are `pytest`, `pillow` and `cryptography`. Do not add a dependency without a stated reason.

## Commands

- `make install`: builds `.venv` with uv and installs the package with dev extras.
- `make test`: runs the suite offline. `make test T=tests/test_cli.py` runs one file.
- `make vendored-verify`: checks the vendored trust lists and samples against `SOURCES.json`, offline.
- `make vendored`: downloads the vendored files again. This needs network. Commit the files and `SOURCES.json` together.
- `make validate-real`: checks your own provider samples against `tests/fixtures/real/expected.json`.
- Run the CLI as `.venv/bin/wmd` or `.venv/bin/python -m watermark_detector`.

## Layout

Modules in `src/watermark_detector/`:

- `__main__.py`: entry point for `python -m watermark_detector`.
- `aigc_label.py`: reads China's GB 45438 implicit AI-content label. Unsigned metadata.
- `bmff.py`: minimal ISO-BMFF (MP4/MOV) reader for metadata key/value items.
- `c2pa_reader.py`: reads C2PA manifests with an explicit trust context.
- `capabilities.py`: what can and cannot be checked per provider and modality, as research data.
- `certs.py`: pulls certificates out of a signed file so the user can pin an anchor.
- `cli.py`: command line entry point and exit codes.
- `containers.py`: finds embedded images inside OOXML and PDF files, with limits.
- `detect.py`: runs every check that applies to one file and builds a report. Holds `MAX_INPUT_BYTES`.
- `model.py`: report data model shared by all modules. Holds the `Verdict` values.
- `report.py`: turns reports into JSON and text. Holds the JSON schema id.
- `sniff.py`: decides what kind of file a byte buffer is.
- `text_verifiers.py`: opt-in remote text verifiers. Endpoints come from the user's TOML file.
- `textio.py`: pulls plain text out of text, DOCX and PDF files.
- `validate.py`: checks real provider samples against a user-written manifest of expectations.
- `xmp.py`: finds unsigned IPTC AI markers in XMP packets.

Subpackages and other folders:

- `providers/`: one module per provider (`claude.py`, `gemini.py`, `gpt.py`, `zai.py`) with its profile, plus `__init__.py` for C2PA attribution rules and the `PROFILES` registry.
- `trust/`: vendored C2PA trust anchors and `SOURCES.json`.
- `scripts/fetch_vendored.py`: downloads and verifies the vendored trust files.
- `tests/`: one `test_<module>.py` per module. `tests/fixtures/build.py` builds signed and labelled samples at test time, with the throwaway PKI in `tests/fixtures/pki.py`. `tests/fixtures/mock_verifier.py` is a local HTTP stand-in for a remote verifier. `tests/fixtures/third_party/` holds vendored c2pa-python samples. `tests/fixtures/real/` is for the user's own samples.
- `docs/`: `43.01-research`, `43.02-validation` and `43.03-guide`.

## Rules for changes

- Tests stay offline. Fixtures are generated at test time, not committed. Only `tests/fixtures/third_party/` is vendored.
- `tests/conftest.py` points `WMD_CONFIG` at a file that does not exist, so tests never read a user's config.
- No network without `--remote`. The C2PA reader keeps remote manifest fetch and OCSP off.
- Remote verifiers: no hardcoded endpoints. https only, with http allowed only for localhost. Keys come from the environment variable named in the config. Keys are never printed, logged or written to a report.
- C2PA attribution comes only from the signer certificate subject. GB 45438 attribution comes only from the USCC in `ContentProducer`. Never use names in claims, generator strings or file names.
- Unsigned metadata is always `unsigned_hint`.
- Producer codes of individuals are redacted in output (`redact_code` in `aigc_label.py`).
- The JSON schema id `watermark-detector/report@1` (in `report.py`) changes when a field is renamed or removed. Update the guide when it does.
- CLI exit codes are a contract: detect 0/1, certs 0/1, validate 0/3/1, usage 2. `tests/test_cli.py` covers them.
- A new verdict or coverage status must be added to the guide. `tests/test_guide.py` checks this.
- `capabilities.py` is research as data. A changed row needs the research note and `docs/43.01-research/sources.md` updated together.
- Adding a provider means: a module in `providers/`, registration in `PROFILES` in `providers/__init__.py`, rows in `capabilities.py`, fixtures in `tests/fixtures/build.py`, tests, and a research note.
- Inputs are capped at 512 MiB (`MAX_INPUT_BYTES` in `detect.py`). Container scans stay bounded by the limits in `containers.py`.
- Trust lists change only through `make vendored`.

## Docs

- Block folders are named `NN.NN-name`. File names are lowercase kebab-case.
- Every folder has an `index.md` that links each note with a relative Markdown link. Each note links back to its index.
- YAML frontmatter keys are `tema`, `tipo` (`índice` or `nota`), `proyecto`, `creada`, `actualizada`, `estado`, `aliases` and `tags`. Bump `actualizada` on every edit.
- Research claims carry a [P] or [S] tag and an E# or L# id. The ids are listed in `docs/43.01-research/sources.md`. Mark unconfirmed facts as (unverified).
- `tests/test_docs.py` enforces these rules.

## Writing

README, guide, this file and code comments use plain English with short sentences. State facts with a source. Use no emoji and no em dashes. Never state a number that the sources do not give.

## Before you finish

- `make test` passes.
- Never commit `.venv/`, build output, `*.egg-info/`, real samples (`tests/fixtures/real/samples/`, `tests/fixtures/real/expected.json`), credentials, or local tool folders.
- Machine-specific ignores belong in `.git/info/exclude`, not in `.gitignore`.
