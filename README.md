# Stock Upload Toolkit

This repo provides utilities to auto-generate SEO-friendly metadata for stock images and upload them to Shutterstock and Adobe Stock.

## Tools
- **stockmate.py** – Batch generate titles, descriptions and keywords using OpenAI. Can write IPTC metadata and export CSV.
- **uploader.py** – Uses `stockmate` to create metadata and uploads images directly to stock marketplaces. Requires tokens in `SHUTTERSTOCK_TOKEN` and `ADOBE_TOKEN` environment variables.

## Example
```bash
python uploader.py ./photos --site both --max-kw 40
```

`uploader.py` iterates through the folder, generates metadata, and posts each image with its keywords and title to the selected agencies.
