#!/usr/bin/env python3
"""
StockMate v0.5.1 (hotfix)

Batch-generate titles, descriptions, and ordered keywords for stock photos,
then write them into IPTC metadata (so Shutterstock & Adobe Stock prefill on upload)
and optionally export a CSV.

Fixes in v0.5.1:
- ✅ Fix SyntaxError: unterminated string in USER_PROMPT
- ✅ Fix stray newline in _force_json error message
- ✅ Add --selftest with basic unit tests (no network required)
- ✅ Safer debug when openai package is missing

Dependencies:
    pip install --upgrade "openai>=1.40,<2" pillow tqdm

Optional (recommended) for IPTC writing:
    ExifTool (https://exiftool.org/) must be installed and available in PATH.

Environment:
    Set your OpenAI API key in OPENAI_API_KEY

Example:
    python stockmate.py D:/photos/batch --lang en --max-kw 30 --write-iptc --csv out/shutterstock.csv
    python stockmate.py ./in --lang en,zh --max-kw 40 --write-iptc --csv out/adobe.csv

Notes:
- JPEG/JPG/TIF are fully supported for IPTC embedding. PNG will export CSV only.
- Keyword order in the CSV is preserved; top-10 are the strongest for Adobe.
- Bilingual mode writes English keywords first, then Chinese.

MIT License.
"""

from __future__ import annotations
import argparse
import base64
import csv
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image
from tqdm import tqdm

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

SUPPORTED_EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}

# ----------------------------- Data models ----------------------------- #

@dataclass
class Meta:
    title: str
    description: str
    keywords_en: List[str]
    keywords_zh: List[str]

    def merged_keywords(self, lang_pref: str) -> List[str]:
        if lang_pref == "en":
            return self._dedupe(self.keywords_en)
        if lang_pref == "zh":
            return self._dedupe(self.keywords_zh)
        # both: English first, then Chinese
        return self._dedupe(self.keywords_en + self.keywords_zh)

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for k in items:
            k = (k or "").strip()
            if not k:
                continue
            low = k.lower()
            if low in seen:
                continue
            seen.add(low)
            out.append(k)
        return out

# ----------------------------- OpenAI VLM ------------------------------ #

def _b64_image(path: Path) -> str:
    with path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

SYSTEM_PROMPT = (
    "You are a seasoned microstock editor. Given an image, return JSON with: "
    "title (<=60 chars, natural, includes important nouns), "
    "description (<=220 chars, specific, no keywords spam), "
    "keywords_en (list, up to {max_kw}, single words/short 2-3 word phrases, ordered by importance; top 10 strongest), "
    "keywords_zh (list, up to {max_kw}, ordered to mirror English; translate & localize, keep proper nouns). "
    "No salesy words. No private info. Output ONLY JSON."
)

USER_PROMPT = (
    "Task: Analyze the image and produce high-quality stock metadata.\n"
    "Context: Buyers search by specific subjects, objects, locations, styles, moods, seasons, colors, weather, camera angles.\n"
    "Rules:\n"
    " - Avoid duplicate variants (singular/plural duplicates).\n"
    " - Avoid brand names, people names, or trademarks unless clearly generic or editorial.\n"
    " - Prefer nouns and concrete terms; add 2-3 style/mood words when relevant.\n"
    " - Use American English for English keywords.\n"
    " - Chinese should be 简体中文.\n"
    "Return strict JSON with keys: title, description, keywords_en, keywords_zh."
)

class AIGenerator:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        if OpenAI is None:
            raise RuntimeError("openai package not installed. Run: pip install 'openai>=1.40,<2'")
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature

    def for_image(self, img_path: Path, max_kw: int) -> Meta:
        sys_prompt = SYSTEM_PROMPT.format(max_kw=max_kw)
        b64 = _b64_image(img_path)
        messages = [
            {"role": "system", "content": sys_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{img_path.suffix[1:].lower()};base64,{b64}",
                        },
                    },
                ],
            },
        ]
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            max_tokens=500,
        )
        text = resp.choices[0].message.content or "{}"
        data = _force_json(text)
        return Meta(
            title=data.get("title", "").strip(),
            description=data.get("description", "").strip(),
            keywords_en=[s.strip() for s in data.get("keywords_en", []) if s and str(s).strip()],
            keywords_zh=[s.strip() for s in data.get("keywords_zh", []) if s and str(s).strip()],
        )


class MockAIGenerator:
    def __init__(self) -> None:
        pass

    def _slug_to_title(self, stem: str) -> str:
        cleaned = re.sub(r"[_\-]+", " ", stem).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        title = cleaned.title()[:60]
        return title or "Untitled"

    def _english_keywords(self, stem: str, max_kw: int) -> List[str]:
        raw = re.split(r"[^a-zA-Z]+", stem.lower())
        tokens = [t for t in raw if len(t) > 1]
        # dedupe preserving order
        seen = set()
        kws: List[str] = []
        for t in tokens:
            if t in seen:
                continue
            seen.add(t)
            kws.append(t)
        return kws[:max_kw]

    def _to_chinese(self, kws_en: List[str]) -> List[str]:
        mapping = {
            "sunset": "日落",
            "sunrise": "日出",
            "mountain": "山",
            "mountains": "群山",
            "forest": "森林",
            "tree": "树",
            "trees": "树木",
            "city": "城市",
            "night": "夜晚",
            "street": "街道",
            "sky": "天空",
            "road": "道路",
            "river": "河流",
            "sea": "大海",
            "ocean": "海洋",
            "beach": "海滩",
            "flower": "花",
            "cat": "猫",
            "dog": "狗",
            "landscape": "风景",
            "travel": "旅行",
            "nature": "自然",
            "red": "红色",
            "blue": "蓝色",
            "green": "绿色",
            "yellow": "黄色",
            "orange": "橙色",
            "pink": "粉色",
            "purple": "紫色",
            "white": "白色",
            "black": "黑色",
            "brown": "棕色",
            "gray": "灰色",
        }
        out: List[str] = []
        seen = set()
        for w in kws_en:
            zh = mapping.get(w.lower(), w)
            if zh in seen:
                continue
            seen.add(zh)
            out.append(zh)
        return out

    def for_image(self, img_path: Path, max_kw: int) -> Meta:
        stem = img_path.stem
        title = self._slug_to_title(stem)
        description = f"Stock photo of {title.lower()}."
        k_en = self._english_keywords(stem, max_kw)
        k_zh = self._to_chinese(k_en)
        return Meta(title=title, description=description, keywords_en=k_en, keywords_zh=k_zh)

# ----------------------------- Utilities ------------------------------- #

def _force_json(s: str) -> dict:
    s = (s or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*", "", s).strip()
        s = s[:-3] if s.endswith("```") else s
    try:
        return json.loads(s)
    except Exception:
        # Try to find the first JSON object
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    raise ValueError("Model did not return valid JSON; raw=" + s[:800])

# ----------------------------- IPTC writing ---------------------------- #

def has_exiftool() -> bool:
    try:
        subprocess.run(["exiftool", "-ver"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        return True
    except Exception:
        return False

def write_iptc(img: Path, title: str, description: str, keywords: List[str]) -> Tuple[bool, str]:
    """Write IPTC ObjectName (Title), Caption-Abstract (Description), and Keywords using exiftool.
    Returns (ok, message)."""
    if img.suffix.lower() not in {".jpg", ".jpeg", ".tif", ".tiff"}:
        return False, "IPTC embedding is supported for JPEG/TIFF only; skipped"
    if not has_exiftool():
        return False, "ExifTool not found; skipped IPTC write"
    # Build command
    cmd = [
        "exiftool",
        "-overwrite_original",
        f"-IPTC:ObjectName={title[:60]}",
        f"-IPTC:Caption-Abstract={description[:220]}",
    ]
    for kw in keywords:
        if kw:
            cmd.append(f"-IPTC:Keywords={kw}")
    cmd.append(str(img))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            return False, f"ExifTool error: {r.stderr.strip() or r.stdout.strip()}"
        return True, "IPTC written"
    except Exception as e:
        return False, f"ExifTool failed: {e}"

# ----------------------------- CSV export ------------------------------ #

def export_csv(rows: List[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["filename", "title", "description", "keywords"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ----------------------------- Debug helpers --------------------------- #

def debug_info(model: str) -> None:
    print("=== DEBUG INFO ===")
    print("Python:", sys.version.split()[0])
    try:
        import openai as _openai
        print("openai:", getattr(_openai, "__version__", "unknown"))
    except Exception as e:
        print("openai: not installed", e)
    print("Platform:", platform.platform())
    print("OPENAI_API_KEY set:", bool(os.getenv("OPENAI_API_KEY")))
    print("ExifTool in PATH:", has_exiftool())
    # Connectivity test (tiny):
    try:
        client = OpenAI() if OpenAI is not None else None
        if client is None:
            raise RuntimeError("openai package not installed")
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "pong"},
                {"role": "user", "content": "ping"},
            ],
            max_tokens=4,
        )
        print("Model reachable:", True, "id=", getattr(r, "id", "-"))
    except Exception as e:
        print("Model reachable:", False, "reason=", str(e)[:300])

# ----------------------------- Self tests ------------------------------ #

def run_selftests() -> int:
    print("=== RUNNING SELFTESTS (no network) ===")
    # 1) USER_PROMPT integrity
    assert isinstance(USER_PROMPT, str) and "high-quality stock metadata" in USER_PROMPT
    assert "Return strict JSON" in USER_PROMPT

    # 2) _force_json on clean JSON
    d = _force_json('{"title":"T","description":"D","keywords_en":["a"],"keywords_zh":["甲"]}')
    assert d["title"] == "T" and d["description"] == "D"

    # 3) _force_json on fenced block
    d2 = _force_json("""```json\n{\n \"x\": 1\n}\n```""")
    assert d2["x"] == 1

    # 4) _force_json on noisy text + JSON
    d3 = _force_json("noise before {\n \"y\": 2\n} noise after")
    assert d3["y"] == 2

    # 5) Deduplication & order
    m = Meta("t","d", ["Tree","tree","Forest","forest"], ["树","森林","树"]) 
    assert m._dedupe(["A","a","B","a"]) == ["A","B"]
    assert m.merged_keywords("en") == ["Tree","Forest"]
    assert m.merged_keywords("zh") == ["树","森林"]
    assert m.merged_keywords("en,zh") == ["Tree","Forest","树","森林"]

    # 6) write_iptc refusal on PNG
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.png"
        Image.new("RGB", (1,1), (255,255,255)).save(p)
        ok, msg = write_iptc(p, "t", "d", ["k"]) 
        assert ok is False and "JPEG/TIFF" in msg

    # 7) parse_args smoke test
    ap = parse_args(["./in", "--lang", "en,zh", "--max-kw", "30"]) 
    assert ap.lang == "en,zh" and ap.max_kw == 30

    print("ALL TESTS PASSED")
    return 0

# ----------------------------- Main logic ------------------------------ #

def process_folder(
    in_dir: Path,
    lang: str,
    max_kw: int,
    write_iptc_flag: bool,
    csv_path: Optional[Path],
    model: str,
    temperature: float,
    debug: bool,
    mock: bool = False,
) -> None:
    if debug:
        debug_info(model)

    images = [p for p in in_dir.rglob("*") if p.suffix.lower() in SUPPORTED_EXTS]
    if not images:
        print("No images found.")
        return

    ai = MockAIGenerator() if mock else AIGenerator(model=model, temperature=temperature)
    rows: List[dict] = []

    for p in tqdm(images, desc="Processing", unit="img"):
        try:
            meta = ai.for_image(p, max_kw=max_kw)
            # Cap keywords for Adobe (49). Shutterstock accepts up to 50.
            kws = meta.merged_keywords(lang)[: max_kw]
            title = meta.title
            desc = meta.description

            if write_iptc_flag:
                ok, msg = write_iptc(p, title, desc, kws)
                tqdm.write(f"[{p.name}] IPTC: {msg}")

            rows.append(
                {
                    "filename": p.name,
                    "title": title,
                    "description": desc,
                    "keywords": "; ".join(kws),  # semi-colon separated
                }
            )
        except Exception as e:
            tqdm.write(f"[{p.name}] ERROR: {e}")

    if csv_path:
        export_csv(rows, csv_path)
        print(f"CSV saved: {csv_path}")

# ----------------------------- CLI ------------------------------------ #

def parse_args(argv: List[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="StockMate — batch stock metadata helper")
    ap.add_argument("in_dir", type=str, help="Input folder containing images")
    ap.add_argument("--lang", default="en", help="en | zh | en,zh (default: en)")
    ap.add_argument("--max-kw", type=int, default=30, help="Max keywords per image (default 30)")
    ap.add_argument("--write-iptc", action="store_true", help="Write IPTC into JPEG/TIFF via ExifTool")
    ap.add_argument("--csv", type=str, default=None, help="Optional path to export a CSV (e.g., out/shutterstock.csv)")
    ap.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI vision model (default gpt-4o-mini)")
    ap.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature (default 0.2)")
    ap.add_argument("--debug", action="store_true", help="Print environment & model connectivity diagnostics")
    ap.add_argument("--selftest", action="store_true", help="Run built-in tests and exit")
    ap.add_argument("--mock", action="store_true", help="Use MockAIGenerator to derive metadata from filenames")
    return ap.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    if args.selftest:
        return run_selftests()

    in_dir = Path(args.in_dir)
    if not in_dir.exists():
        print(f"Input folder not found: {in_dir}")
        return 2

    # Normalize language preference
    lang = args.lang.replace(" ", "")
    if lang not in {"en", "zh", "en,zh"}:
        print("--lang must be one of: en | zh | en,zh")
        return 2

    csv_path = Path(args.csv) if args.csv else None

    try:
        process_folder(
            in_dir=in_dir,
            lang=lang,
            max_kw=int(args.max_kw),
            write_iptc_flag=bool(args.write_iptc),
            csv_path=csv_path,
            model=str(args.model),
            temperature=float(args.temperature),
            debug=bool(args.debug),
            mock=bool(getattr(args, "mock", False)),
        )
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))