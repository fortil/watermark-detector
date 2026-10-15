# watermark-detector

A command line tool and Python library that looks for AI provenance signals in files from Claude, Gemini, GPT and Z.AI. It only detects. It does not remove, alter or hide any mark.

For a step-by-step walkthrough, see the [usage guide](docs/43.03-guide/usage-guide.md).

## What it detects

| Provider | Text | Image | Document | Video |
|---|---|---|---|---|
| Claude | Needs Anthropic's detector (`--remote`) | C2PA, local | C2PA and embedded images, local | not read |
| Gemini | Not detectable by third parties | C2PA and IPTC XMP, local | C2PA and embedded images, local | not read |
| GPT | Needs OpenAI's detector (`--remote`) | C2PA, local | C2PA and embedded images, local | not read |
| Z.AI | No documented mark | GB 45438 label, local | GB 45438 label, local | GB 45438 label, local |

Run `wmd providers` for the full table, with sources and how to check each signal by hand.

## What it cannot detect

- Text watermarks (Claude, Gemini, GPT) need the provider's keys. The tool has no local detector. For Claude and GPT you can configure a remote verifier once you have access.
- SynthID pixel watermarks are not read locally. Check them by hand: synthid.com (Google does not document its daily limit, so this README gives no number) or the Gemini app, which allows about 10 image checks per rolling 24 hours.
- Absence of a signal does not mean a file is human-made. Screenshots, re-saving and format conversion remove C2PA and metadata.

## Install

```
make install
```

This builds `.venv` with Python 3.12 through uv and installs the package with its dev tools. Python 3.11 or later is required.

## Commands

```
wmd detect PATH [PATH ...] [--json] [--anchors PEM_FILE]... [--remote] [--config TOML]
wmd providers [--json]
wmd certs PATH [-o OUT_PEM]
wmd validate MANIFEST [--remote] [--config TOML]
```

Examples:

```
wmd detect picture.png
wmd detect --json report.docx notes.pdf
wmd providers
wmd certs picture.png -o chain.pem
wmd validate tests/fixtures/real/expected.json
```

Exit codes:

- `detect`: 0 when every file was read without errors, 1 if a path is missing or unreadable or a report has errors.
- `certs`: 0 on success, 1 if no certificates are found.
- `validate`: 0 if all samples pass, 3 if any fails, 1 if the manifest cannot be read.
- Usage errors, and running `wmd` with no arguments, exit with 2.

Verdicts:

- `confirmed`: a provider signer whose chain ends at a trusted anchor.
- `claimed`: a provider signer with an intact signature, but the chain is not trusted.
- `via_ingredient`: a provider manifest found as an ingredient, not the active one.
- `invalid`: the signature or content check failed.
- `ai_unknown_provider`: the file says it is AI-generated, signed by someone we do not know.
- `present_other`: C2PA is present, with no provider and no AI source type.
- `unsigned_hint`: unsigned metadata that points at an AI tool (XMP marker or GB 45438 label). Anyone can add or remove it.
- `remote_reference`: the manifest is remote and was not fetched.
- `score`: a remote verifier returned a score.
- `absent`, `skipped`, `not_configured`, `not_run`, `error`: nothing found, not checked, or something failed.

## Pinning an anchor

Anthropic's signing chain is not on the C2PA trust lists, so Claude files are `claimed`. To get `confirmed`, generate a file yourself with the provider, then:

```
wmd certs my-claude-file.png -o chain.pem
wmd detect --anchors chain.pem other-file.png
```

Pin only certificates taken from a file you know is genuine. A certificate you pin is trusted for every file you check afterwards.

## Remote text verifiers

Remote checks are off unless you pass `--remote`. The tool never hardcodes an endpoint, because the providers have not published their specs. Fill in a TOML file (default `~/.config/watermark-detector/verifiers.toml`, or `--config`, or the `WMD_CONFIG` variable) from the provider's documentation:

```toml
[verifiers.claude]
endpoint = "https://PROVIDER-HOST/PATH"
api_key_env = "CLAUDE_DETECTOR_KEY"
score_path = "result.likelihood"
# optional: label_path, auth_header, auth_scheme, text_field, extra_body, timeout_s, max_chars
```

Names can be `claude`, `gemini` or `gpt`. The key is read from the environment variable named in `api_key_env` and is never printed. Endpoints must use https (http only for localhost).

## China's GB 45438 AIGC label

China's labeling rules, in force since 2025-09-01, require AI services to add an implicit label to file metadata. The label is a JSON string with fields such as `Label`, `ContentProducer` and `ProduceID`. Z.AI (Zhipu) images and videos carry it.

The tool reads it from JPEG EXIF `UserComment`, XMP, PNG text chunks, MP4/MOV metadata keys, DOCX custom properties and PDF Info. It attributes a label to a provider only through the company code inside `ContentProducer`. Codes for individuals are redacted in the output.

Things to keep in mind:

- The label is unsigned. Anyone can write it, and a re-save or screenshot removes it, so it is only ever an `unsigned_hint`.
- Z.AI's visible "AI生成" badge and its pixel watermark are not checked.
- Z.AI text has no documented mark.
- Video files are checked only for this label, not for C2PA.

## Validation

```
make test
make validate-real
```

`make test` runs the suite offline on synthetic fixtures. `make validate-real` checks your own provider outputs against `tests/fixtures/real/expected.json`; see `tests/fixtures/real/README.md` for the protocol. The real-sample test is skipped when that file does not exist.

## Limitations

- Detection only, and only the signals listed above.
- C2PA is verified offline against the vendored trust lists (`make vendored` refreshes them) plus your pins.
- Input files are limited to 512 MiB. Office files and PDFs have member and depth limits.
- Reading video C2PA, other video containers and audio is not done.

Sources and research notes are in `docs/`.
