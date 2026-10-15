# Real-sample validation

The synthetic fixtures prove the tool against itself. This folder is for outputs from your own accounts, so the checks also run against what the providers really emit.

## Where things go

- Put samples in `tests/fixtures/real/samples/`. The folder is gitignored.
- Copy `expected.example.json` to `expected.json` in this folder (also gitignored), keep the rows you actually produced and fix the paths.
- Run `make validate-real`, or `make test`. The test `tests/test_real_samples.py` is skipped while `expected.json` does not exist.

## Manifest format

```json
{"version": 1, "samples": [
  {"id": "...", "path": "samples/x.png", "anchors": ["samples/root.pem"],
   "expect": {"layer": "c2pa", "provider": "claude", "verdict_in": ["claimed"]}}
]}
```

- `path` and `anchors` are relative to the manifest folder. `anchors` is optional and holds PEM files to pin for that sample.
- `expect` keys are all optional: `layer`, `provider` (null is allowed), `verdict_in` (a list), `location`, `score_min`, `score_max`. A sample passes when one finding meets every key you give.
- `{"no_provider_signal": true}` passes when no `c2pa`, `xmp` or `aigc-label` finding names a provider with a verdict of confirmed, claimed, via_ingredient, invalid or unsigned_hint.
- `wmd validate` prints `PASS <id>` or `FAIL <id>: <detail>`. It exits 0 if all pass, 3 if any fails, 1 if the manifest cannot be read.

## Protocol

The expectations are as of 2026-10-10. Write down what you actually get: a mismatch is information, not a bug by default.

| # | Provider / modality | How to produce it | Expected | Negative counterpart |
|---|---|---|---|---|
| 1 | Claude PNG | claude.ai with file creation, supported model: "make a 256x256 PNG bar chart as a downloadable file", then download it | c2pa claude/claimed; confirmed after pinning the intermediate taken with `wmd certs` from this same file | A screenshot of it: no provider signal |
| 2 | Claude SVG | "make a simple SVG logo file", then download it | claude/claimed | Re-export through an editor: absent |
| 3 | Claude API | Code execution, then a Files API download | claude/claimed (manifest attached at download) | none |
| 4 | Claude DOCX | "make a .docx report with a chart" | No C2PA provider signal expected (unverified); text-watermark not_run | none |
| 5 | Claude text | At least 400 words of creative prose | not_run without access; with Detection API access, a score | Public-domain text, for example https://www.gutenberg.org/ebooks/1342 |
| 6 | GPT image (ChatGPT) | Generate an image and download it as PNG | gpt/confirmed if OpenAI's chain anchors in the vendored lists, else claimed (unverified until run). If absent, re-check at https://openai.com/research/verify/ | A screenshot: no provider signal |
| 7 | GPT image (API gpt-image-*) | Decode the b64 output to PNG | Same as 6 (unverified) | none |
| 8 | GPT text | An API project with "Allow text watermarking" on (Settings, Text provenance) and at least 400 tokens of prose | not_run unless you have researcher detector access | Public-domain text |
| 9 | Gemini image | Gemini app (Nano Banana), then download | gemini/confirmed expected (unverified until run), maybe also xmp gemini/unsigned_hint. Check SynthID by hand at synthid.com | A screenshot: no provider signal |
| 10 | Gemini text | At least 400 words | Coverage only: no third-party detector exists | none |
| 11 | Human/camera | Your own phone photo; a Pixel photo if you have one | absent or present_other, never gemini | none |
| 12 | Z.AI image (China API) | `open.bigmodel.cn` `POST /api/paas/v4/images/generations` with `model: "glm-image"` (or `cogview-4`) and default parameters; download `data[0].url` within 30 days | aigc-label zai/unsigned_hint at file. By eye, an "AI生成" badge bottom-right is likely | A screenshot: no provider signal |
| 13 | Z.AI image (international API) | `api.z.ai`, same endpoint, `model: "glm-image"` | aigc-label zai/unsigned_hint at file; no badge expected | A screenshot: no provider signal |
| 14 | Z.AI video | `open.bigmodel.cn` `POST /api/paas/v4/videos/generations` with `model: "cogvideox-3"`; poll the async result, then download `video_result[0].url` | kind video; aigc-label zai/unsigned_hint at file | A screenshot of one frame: no provider signal |
| 15 | Z.AI text | chat.z.ai or the chat API, at least 400 words | Coverage only: no mark is documented | none |

## Privacy and legal

- Samples may carry account or device details in their metadata. Do not commit or share them without checking.
- The providers' terms give users rights over their own outputs. That was not re-verified here, so check the current terms before sharing a sample.
- Use only outputs you generated yourself.
