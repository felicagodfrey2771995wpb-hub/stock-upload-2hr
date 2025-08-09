from typing import List, Dict
import csv
import os


def _ensure_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def export_csv(records: List[Dict[str, object]], platform: str, output_csv_path: str) -> None:
    """
    Export metadata list to a platform-specific CSV.

    Supported platforms: 'shutterstock', 'adobe'
    """
    platform = platform.lower()
    _ensure_dir(output_csv_path)

    if platform == "shutterstock":
        # Minimal fields commonly accepted: filename, description, keywords
        fieldnames = ["filename", "description", "keywords"]
        rows = []
        for r in records:
            kws = r.get("keywords", [])
            if isinstance(kws, list):
                kw_str = ", ".join([str(k) for k in kws])
            else:
                kw_str = str(kws)
            rows.append({
                "filename": r.get("filename", ""),
                "description": r.get("description", ""),
                "keywords": kw_str,
            })
    elif platform == "adobe":
        # Adobe Stock typical fields: filename, title, keywords
        fieldnames = ["filename", "title", "keywords"]
        rows = []
        for r in records:
            kws = r.get("keywords", [])
            if isinstance(kws, list):
                kw_str = ", ".join([str(k) for k in kws])
            else:
                kw_str = str(kws)
            rows.append({
                "filename": r.get("filename", ""),
                "title": r.get("title", r.get("description", "")),
                "keywords": kw_str,
            })
    else:
        raise ValueError(f"Unsupported platform: {platform}")

    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)