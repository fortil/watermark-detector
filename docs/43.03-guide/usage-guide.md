---
tema: Usage guide
tipo: nota
proyecto: watermark-detector
creada: 2026-10-15
actualizada: 2026-10-15
estado: activa
aliases: [Usage guide]
tags: [watermark-detector, guide]
---

# Usage guide

This guide shows how to install `wmd`, run each command, and read the reports. The tool only detects. It works offline unless you pass `--remote`. For an overview, see the [README](../../README.md).

## What the tool checks

- **C2PA Content Credentials** (signed). Provider signatures in images, SVG, PDF and Office files.
- **IPTC XMP AI markers** (unsigned). A metadata field that names an AI tool.
- **China's GB 45438 label** (unsigned). A JSON label in file metadata, used by Z.AI.
- **Opt-in remote text verifiers** for Claude, Gemini and GPT. They run only with `--remote` and a config file.

Run `wmd providers` for the full matrix of providers, modalities and checks.

Recognized inputs:

- Images: PNG, JPEG, GIF, WebP, TIFF, AVIF, HEIC.
- SVG.
- PDF.
- DOCX, XLSX and PPTX.
- MP4 and MOV video. Video is checked only for the GB 45438 label.
- UTF-8 plain text.

Other file types exit with `error: unsupported file type`.

## Install

You need Python 3.11 or later. From the repository root, run:

```
make install
```

This needs `uv`. It builds `.venv` with Python 3.12 and installs the package with its dev tools.

Without uv, create a virtual environment with Python 3.11 or later and run `pip install -e '.[dev]'`.

Then run `.venv/bin/wmd`, or activate the environment with `source .venv/bin/activate` and run `wmd`. Check the install with `wmd --version`, which prints `wmd 0.1.0`.

## Quick start

Run this from the repository root:

```
.venv/bin/wmd detect tests/fixtures/third_party/C.jpg
```

The output is:

```
tests/fixtures/third_party/C.jpg [image, image/jpeg]
  c2pa - PRESENT_OTHER @file C2PA Test Signing Cert/C2PA Signer
  coverage:
    claude: C2PA Content Credential (.png .jpg .svg) [checked]
    gemini: C2PA (Google LLC, Google Media Processing Services) [checked]
    gemini: SynthID pixel watermark [manual_check_available]
    gemini: IPTC XMP DigitalSourceType + Credit 'Made with Google AI' [checked]
    gpt: C2PA (OpenAI / OpenAI OpCo, LLC, OpenAI Media Service) [checked]
    gpt: SynthID pixel watermark (since 2026-05-19) [manual_check_available]
    zai: GB 45438 AIGC label (EXIF UserComment; also XMP or PNG text) with Zhipu's producer code [checked]
    zai: Visible 'AI生成' badge, bottom-right [manual_check_available]
    zai: Implicit digital (pixel) watermark named in BigModel docs [not_checkable]
  No provider provenance signal found. This does not show the content is human-made: C2PA, XMP and EXIF/MP4 metadata labels (such as China's GB 45438 AIGC label) are removed by screenshots, re-saving and format conversion, and text watermarks can only be checked with the provider's detector.
```

Each kind of line means the following:

- **Header** `PATH [kind, mime]`: the file as you passed it, with the kind and MIME type the tool detected. The path is relative because the command ran from the repository root.
- **Finding line** `layer provider VERDICT @location`: one line per finding. Here `c2pa` is the layer, `-` means no provider was attributed, `PRESENT_OTHER` is the verdict, and `@file` is the location. When a C2PA signer is known, its organization and common name follow, as `O/CN`. This sample is signed by a test certificate, so it names no provider.
- **Coverage block** `coverage:`: one line per provider signal that applies to this file type, with its status in brackets. The statuses are explained in [Reading a report](#reading-a-report).
- **Absence note**: printed when no provider signal was found. It says that absence does not show the content is human-made.

## Reading a report

### Text format

The text format is the default. It starts with the header line and then prints these lines, in this order:

- One finding line per finding. The verdict is in upper case.
- `note:` lines for `claimed` findings that carry a note.
- `Unsigned metadata: anyone can add or remove it.` when the report has any `aigc-label` finding.
- `error:` lines for errors in the file or the run.
- The `coverage:` block.
- The absence note, when there is no provider signal.

A `-` in place of the provider means no provider was attributed. An unsigned `aigc-label` finding also shows `producer=` and `label=`. A `score` finding shows `score=`.

### JSON format

`wmd detect --json FILE` prints a list with one object per file. Each object has these keys:

- `schema`: the schema id, `watermark-detector/report@1`.
- `tool_version`, `c2pa_sdk`: the versions of this tool and of the C2PA SDK.
- `path`, `kind`, `mime`: the file, as detected.
- `findings`: a list. Each item has `layer`, `verdict`, `provider`, `location` and `evidence`.
- `coverage`: a list. Each item has `provider`, `signal`, `local` and `status`.
- `errors`: a list of error strings.
- `summary`: `provider_signals` (the verdicts seen for each provider), a count of ai_unknown_provider findings, `ai_label_unattributed` (a count of unsigned GB 45438 labels with no provider), and `absence_note` when there is no provider signal.

The layers are:

- `c2pa`: C2PA manifests.
- `xmp`: IPTC XMP markers.
- `aigc-label`: the GB 45438 label.
- `text-watermark`: remote text verifiers, and the `not_run` note when they are off.
- `container`: embedded files in DOCX, XLSX, PPTX and PDF, and scan limits.

Locations are `file` for the file itself. For an embedded image, the location is the member path, for example `word/media/image1.png` in a DOCX. In a PDF, the location looks like `pdf:page1:Im0:obj4`.

Coverage statuses:

| Status | Meaning |
|---|---|
| `checked` | This tool checks the signal locally for this file type. |
| `verifier_run` | A remote text verifier is configured and ran, because `--remote` was passed. |
| `verifier_configured_not_run` | A remote text verifier is configured, but `--remote` was not passed, so it did not run. |
| `not_checkable_locally` | A text signal. It needs a provider's detector, and no verifier is configured for it. |
| `manual_check_available` | The signal can be checked by hand. `wmd providers` gives the method. |
| `not_checkable` | No local check and no manual check is documented. |

## Verdicts

| Verdict | Meaning | What to do |
|---|---|---|
| `confirmed` | A provider signature whose chain ends at a trusted anchor. | Read the signer. Trust it as far as you trust the anchor. |
| `claimed` | A provider signature that is valid, but its chain is not trusted. Claude files are `claimed`. | Pin an anchor to confirm it. See [Pinning a trust anchor](#pinning-a-trust-anchor). |
| `via_ingredient` | A provider manifest found in an ingredient of the file, not in the active manifest. | Check the location to see which part of the file it covers. |
| `invalid` | A provider manifest that fails validation. | Do not rely on it. The file may have been altered. |
| `ai_unknown_provider` | The file says it is AI-generated, but the signer is not a known provider. | Read the signer in the finding line. |
| `present_other` | C2PA is present, with a signer that is not a provider and no AI source type. | Nothing provenance-related. The signer is shown on the line. |
| `unsigned_hint` | Unsigned metadata that names a provider: an XMP marker or a GB 45438 label. | Use it as a lead only. Anyone can add or remove it. |
| `remote_reference` | The C2PA manifest is stored at a remote URL. The tool does not fetch it. | The URL is in `evidence`. Check it yourself if you need the manifest. |
| `absent` | No C2PA manifest in the file. | Nothing to act on. |
| `skipped` | Part of a container was not checked, for example a PDF image with an unsupported encoding. | Check that part by hand if it matters. |
| `score` | A remote text verifier returned a score. | Read the score with the verifier's documentation. |
| `not_configured` | A verifier is set up, but its API key variable is not set. | Set the variable named in `api_key_env`. |
| `not_run` | A verifier is configured, but `--remote` was not passed. | Add `--remote` to run it. |
| `error` | A check failed, for example a network error or a bad response. | Read the reason in `evidence` in the JSON output. |

Absence of a signal does not show that a file is human-made. Screenshots, re-saving and format conversion remove C2PA data and metadata labels.

## Commands

`wmd --help` lists the commands. `wmd --version` prints the version.

### wmd detect

Synopsis: `wmd detect PATH [PATH ...] [--json] [--anchors PEM_FILE]... [--remote] [--config TOML]`

- `PATH`: one or more files to check.
- `--json`: print JSON instead of text.
- `--anchors PEM_FILE`: a trust anchor to pin. Repeat the option for more anchors.
- `--remote`: run the configured remote text verifiers.
- `--config TOML`: the verifier config file. See [Remote text verifiers](#remote-text-verifiers).

Example:

```
wmd detect --json report.docx notes.pdf
```

Exit codes: 0 when every file was read without errors. 1 when a path is missing or unreadable, or a report has errors. 2 for usage errors.

### wmd providers

Synopsis: `wmd providers [--json]`

For each provider and modality, prints whether the signal is checked locally, the signal name, how to check it by hand, and a note. `--json` prints the same data as JSON.

Example:

```
wmd providers
```

Exit codes: 0. 2 for usage errors.

### wmd certs

Synopsis: `wmd certs PATH [-o OUT_PEM]`

Lists the certificates in the C2PA chain of a signed file, one line each. Each line shows the index, the SHA-256 fingerprint, the serial number, and whether the certificate is the active signer. `-o OUT_PEM` writes the chain to a PEM file.

Example:

```
wmd certs picture.png -o chain.pem
```

Exit codes: 0 on success. 1 when the file cannot be read or no certificates are found. 2 for usage errors.

### wmd validate

Synopsis: `wmd validate MANIFEST [--remote] [--config TOML]`

Checks the samples listed in a manifest. Prints `PASS <id>` or `FAIL <id>: <detail>` for each sample. See [Checking your own samples](#checking-your-own-samples).

Example:

```
wmd validate tests/fixtures/real/expected.json
```

Exit codes: 0 when all samples pass. 3 when any sample fails. 1 when the manifest cannot be read. 2 for usage errors.

## Exit codes

| Command | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| `detect` | Every file was read without errors. | A path is missing or unreadable, or a report has errors. | Usage error. | Not used. |
| `providers` | Always, on success. | Not used. | Usage error. | Not used. |
| `certs` | Certificates were listed. | No certificates found, or the file cannot be read. | Usage error. | Not used. |
| `validate` | All samples pass. | The manifest cannot be read. | Usage error. | Any sample fails. |

Running `wmd` with no arguments prints the help and exits with 2.

## Documents and videos

- **DOCX, XLSX, PPTX and PDF** are checked at file level for C2PA, XMP and the GB 45438 label. Embedded images are checked too.
- **PDF images** with encodings the tool does not support are counted as `skipped` in a `container` finding.
- **Scan limits**: when a container cannot be scanned fully (a bad archive, a bad PDF, or too many members), a `container` finding with verdict `error` says so.
- **Video** (MP4 and MOV) is checked only for the GB 45438 label, in the `moov/udta/meta` metadata. C2PA is not read from video.
- **Remote text verifiers** receive the extracted text of plain text, DOCX and PDF files. The text is cut to `max_chars` before it is sent.

## Pinning a trust anchor

Claude files are `claimed`, because Anthropic is not on the official C2PA trust lists. To confirm them, pin a certificate from a file you know is genuine:

1. Generate a file yourself with the provider, so you know it is genuine.
2. List its chain with `wmd certs that-file.png -o chain.pem`. The active signer is marked.
3. Check another file with the pin: `wmd detect --anchors chain.pem other-file.png`. Matching files show `confirmed` with `trusted_via: user-anchor`.

A pinned certificate is trusted for every later check. Pin only certificates from files you have good reason to trust. For the research behind this, see [C2PA trust](../43.01-research/c2pa-trust.md).

## Remote text verifiers

Remote checks are off unless you pass `--remote`. The tool does not hardcode endpoints. You set them in a TOML file.

The config file is found in this order:

1. The path given with `--config`.
2. The path in the `WMD_CONFIG` environment variable.
3. `~/.config/watermark-detector/verifiers.toml`.

Example, using the names from the README:

```toml
[verifiers.claude]
endpoint = "https://PROVIDER-HOST/PATH"
api_key_env = "CLAUDE_DETECTOR_KEY"
score_path = "result.likelihood"
# optional: label_path, auth_header, auth_scheme, text_field, extra_body, timeout_s, max_chars
```

The table name sets the verifier. The names are `claude`, `gemini` and `gpt`. No other name is accepted.

| Key | Required | Default | Meaning |
|---|---|---|---|
| `endpoint` | yes | none | URL that receives the text. |
| `api_key_env` | yes | none | Name of the environment variable that holds the key. |
| `score_path` | yes | none | Path to the score in the JSON response. |
| `auth_header` | no | `Authorization` | Header that carries the key. |
| `auth_scheme` | no | `Bearer` | Prefix written before the key in that header. |
| `text_field` | no | `text` | Name of the request field that holds the text. |
| `extra_body` | no | `{}` | Extra fields added to the request body. |
| `label_path` | no | empty | Path to a label in the response. |
| `timeout_s` | no | `30.0` | Request timeout, in seconds. |
| `max_chars` | no | `100000` | Maximum number of characters sent. |

Rules:

- The endpoint must use https. Plain http is accepted only for `localhost` and `127.0.0.1`.
- The key is read from the environment variable named in `api_key_env`. The tool never prints it.
- Without `--remote`, a configured verifier shows as `not_run`.

## Checking your own samples

`make validate-real` checks your own provider outputs against a manifest.

1. Copy `tests/fixtures/real/expected.example.json` to `tests/fixtures/real/expected.json`, keep the rows you actually produced, and fix the paths.
2. Put the sample files in `tests/fixtures/real/samples/`.
3. Run `make validate-real`.

Both the manifest and the samples folder are gitignored. Read the [real-sample README](../../tests/fixtures/real/README.md) for the manifest format, and the [Real-samples protocol](../43.02-validation/real-samples-protocol.md) for which files to produce. Check the metadata of a sample before you share it.

## Using it from Python

```python
from watermark_detector.detect import DetectOptions, detect_path
from watermark_detector.report import report_to_dict

report = detect_path("tests/fixtures/third_party/C.jpg", DetectOptions())
for f in report.findings:
    print(f.layer, f.provider, f.verdict, f.location)
print(report_to_dict(report)["summary"])
```

`DetectOptions(anchors_pem=(pem_text,), remote=True, config_path=Path(...))` sets the same options as the command line flags: pinned anchors as PEM text, remote verifiers, and the config file.

`render_text` and `render_json` in `watermark_detector.report` produce the same output as the text and JSON formats.

The package is at version 0.1.0. The Python API may change before 1.0. The JSON `schema` id changes when the JSON format changes.

## Troubleshooting

- `wmd` with no arguments prints the help and exits with 2.
- `error: cannot read file: FileNotFoundError`: the path does not exist or cannot be opened. The exception name after the colon varies, for example `PermissionError`.
- `error: unsupported file type`: the file is not one of the recognized inputs.
- `error: file too large`: the file is over 512 MiB.
- `error: verifier config error: ...`: the config file has a problem. Examples: `unknown verifier name: ...` (the names are `claude`, `gemini` and `gpt`), or `verifier NAME: endpoint must be https (http only for localhost)`.
- `cannot read anchors: FileNotFoundError` (exit 1): a `--anchors` file cannot be read. The exception name varies.
- `no certificates found` (exit 1): `wmd certs` found no certificate chain in the file.
- `manifest error: ...` (exit 1): `wmd validate` cannot read or parse the manifest.

## Limits

- Text watermarks need the provider's detector and keys. The tool has no local text detector.
- SynthID pixel watermarks are not read locally. Check them by hand.
- Screenshots and re-saves remove metadata, so a missing signal proves nothing.
- Z.AI's visible badge and its pixel watermark are not checked.

## Running the tests

- `make test` runs the suite offline. It builds its fixtures at test time.
- `make vendored-verify` checks the vendored files against their SHA-256 values in `SOURCES.json`, offline.

Back to [Guide](index.md).
