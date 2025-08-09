#!/usr/bin/env python3
"""Upload images to Shutterstock and Adobe Stock with auto-generated metadata.

This script uses the metadata generation from ``stockmate`` and sends uploads
via HTTPS to Shutterstock and Adobe Stock contributor APIs. Credentials are
read from the environment variables ``SHUTTERSTOCK_TOKEN`` and ``ADOBE_TOKEN``.
The script processes all images in a folder, generating SEO-friendly titles and
keywords before uploading to the selected marketplaces.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

import requests
from tqdm import tqdm

from stockmate import AIGenerator, SUPPORTED_EXTS


def _iter_images(folder: Path) -> Iterable[Path]:
    for p in folder.rglob("*"):
        if p.suffix.lower() in SUPPORTED_EXTS:
            yield p


def upload_shutterstock(img: Path, meta) -> dict:
    token = os.getenv("SHUTTERSTOCK_TOKEN")
    if not token:
        raise RuntimeError("SHUTTERSTOCK_TOKEN not set")
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": img.open("rb")}
    data = {
        "title": meta.title,
        "description": meta.description,
        "keywords": ",".join(meta.merged_keywords("en")),
    }
    resp = requests.post(
        "https://contributor-api.shutterstock.com/v2/images",  # official endpoint may differ
        headers=headers,
        files=files,
        data=data,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def upload_adobe(img: Path, meta) -> dict:
    token = os.getenv("ADOBE_TOKEN")
    if not token:
        raise RuntimeError("ADOBE_TOKEN not set")
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": img.open("rb")}
    data = {
        "title": meta.title,
        "description": meta.description,
        "keywords": ",".join(meta.merged_keywords("en")),
    }
    resp = requests.post(
        "https://stock.adobe.io/Rest/Media/Upload",  # official endpoint may differ
        headers=headers,
        files=files,
        data=data,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    ap = argparse.ArgumentParser(description="Auto-upload images to stock sites")
    ap.add_argument("folder", type=Path, help="Folder containing images")
    ap.add_argument("--site", choices=["shutterstock", "adobe", "both"], default="both")
    ap.add_argument("--max-kw", type=int, default=30, help="Max keywords per image")
    args = ap.parse_args()

    ai = AIGenerator()
    for img in tqdm(list(_iter_images(args.folder)), desc="Uploading", unit="img"):
        meta = ai.for_image(img, max_kw=args.max_kw)
        if args.site in {"shutterstock", "both"}:
            upload_shutterstock(img, meta)
        if args.site in {"adobe", "both"}:
            upload_adobe(img, meta)


if __name__ == "__main__":  # pragma: no cover
    main()
