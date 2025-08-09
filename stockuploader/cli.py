import os
import sys
import argparse
from typing import List
from glob import glob

from .generator import generate_metadata
from .exporters import export_csv
from .iptc_writer import write_metadata_with_exiftool, write_xmp_sidecar

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def find_images(input_dir: str) -> List[str]:
    paths: List[str] = []
    for ext in SUPPORTED_EXTS:
        paths.extend(glob(os.path.join(input_dir, f"**/*{ext}"), recursive=True))
    return sorted(paths)


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stockuploader",
        description="Generate stock metadata and export CSV for Shutterstock/Adobe; optionally write IPTC/XMP.",
    )
    parser.add_argument("input", help="Input folder containing images")
    parser.add_argument("--lang", default="en", help="Language code for generated text, e.g., en or zh")
    parser.add_argument("--provider", default="heuristic", choices=["heuristic", "openai"], help="Metadata generation provider")
    parser.add_argument("--outdir", default="./out", help="Output directory")
    parser.add_argument("--platforms", default="shutterstock,adobe", help="Comma-separated list: shutterstock,adobe")
    parser.add_argument("--write-iptc", action="store_true", help="Write IPTC/XMP into images (uses exiftool if available; else XMP sidecar)")
    parser.add_argument("--max-keywords", type=int, default=49, help="Max keywords per image (Adobe commonly 49)")

    args = parser.parse_args(argv)

    input_dir = os.path.abspath(args.input)
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    images = find_images(input_dir)
    if not images:
        print("No images found.")
        return 1

    records = []
    for p in images:
        md = generate_metadata(p, lang=args.lang, provider=args.provider, max_keywords=args.max_keywords)
        records.append(md)
        if args.write_iptc:
            ok = write_metadata_with_exiftool(p, md["title"], md["description"], md["keywords"])  # type: ignore
            if not ok:
                # Fallback to XMP sidecar
                write_xmp_sidecar(p, md["title"], md["description"], md["keywords"])  # type: ignore

    platforms = [s.strip().lower() for s in args.platforms.split(",") if s.strip()]
    if "shutterstock" in platforms:
        export_csv(records, "shutterstock", os.path.join(outdir, "shutterstock.csv"))
    if "adobe" in platforms:
        export_csv(records, "adobe", os.path.join(outdir, "adobe.csv"))

    print(f"Processed {len(records)} images. CSV written to: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())