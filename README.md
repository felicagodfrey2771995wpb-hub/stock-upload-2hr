# StockUploader (MVP)

Generate SEO-ready keywords, titles, and descriptions for stock images and export CSVs for Shutterstock and Adobe Stock. Optionally embed IPTC/XMP (via exiftool) or write XMP sidecars.

## Quick start

1. Create a Python venv and install dependencies:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Run on a folder of images:

```bash
python -m stockuploader ./samples --lang zh --provider heuristic --outdir ./out --platforms shutterstock,adobe --write-iptc
```

- `--provider openai` uses OpenAI vision/text if `OPENAI_API_KEY` is set; otherwise it falls back to a heuristic.
- If `exiftool` is available, IPTC/XMP will be embedded into JPEGs; otherwise `.xmp` sidecars are written.

3. Outputs

- `out/shutterstock.csv`
- `out/adobe.csv`
- Optional: Modified images with embedded IPTC/XMP or sidecar `.xmp` files.

## Notes

- Platforms typically accept embedded IPTC/XMP metadata. CSV formats vary; this MVP writes minimal fields commonly accepted:
  - Shutterstock: `filename, description, keywords`
  - Adobe Stock: `filename, title, keywords`
- Keywords are comma-separated. Adjust limits with `--max-keywords` (Adobe commonly up to 49).
- Always review auto-generated text before submission for accuracy and compliance.

## OpenAI Provider (optional)

Set environment variables:

```bash
export OPENAI_API_KEY=sk-...  # your key
export OPENAI_MODEL=gpt-4o-mini  # optional, defaults to gpt-4o-mini
```

Then run with `--provider openai`.

## Disclaimer

Uploader automation to contributor portals may be restricted by platform ToS. Prefer embedding IPTC/XMP and using official uploaders/FTP where provided.