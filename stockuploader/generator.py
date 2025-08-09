import os
import re
import base64
from typing import List, Dict, Tuple, Optional

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


COMMON_STOPWORDS = {
    "the", "a", "an", "and", "of", "in", "on", "to", "for", "with", "by",
    "at", "from", "is", "are", "be", "this", "that", "these", "those", "photo",
    "image", "picture", "img", "final", "edit", "copy", "version"
}

BASIC_COLOR_MAP: List[Tuple[str, Tuple[int, int, int]]] = [
    ("red", (220, 50, 50)),
    ("orange", (240, 150, 60)),
    ("yellow", (240, 220, 70)),
    ("green", (80, 170, 90)),
    ("cyan", (80, 200, 200)),
    ("blue", (70, 110, 230)),
    ("purple", (150, 80, 190)),
    ("pink", (230, 120, 170)),
    ("brown", (150, 110, 80)),
    ("black", (20, 20, 20)),
    ("white", (240, 240, 240)),
    ("gray", (128, 128, 128)),
]


def _tokenize_filename(path: str) -> List[str]:
    name = os.path.splitext(os.path.basename(path))[0]
    # Replace separators with space and split
    name = re.sub(r"[\-_.,]+", " ", name)
    raw_tokens = re.split(r"\s+", name)
    tokens: List[str] = []
    for t in raw_tokens:
        t_norm = re.sub(r"[^a-zA-Z0-9]", "", t).lower()
        if not t_norm:
            continue
        if t_norm.isdigit():
            continue
        if len(t_norm) <= 2:
            continue
        if t_norm in COMMON_STOPWORDS:
            continue
        tokens.append(t_norm)
    # Deduplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


def _nearest_color_name(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    best_name = "color"
    best_dist = 1e9
    for name, (cr, cg, cb) in BASIC_COLOR_MAP:
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


def _dominant_colors(image_path: str, k: int = 4) -> List[str]:
    if Image is None:
        return []
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize((256, 256))
        # Quantize to get dominant palette
        q = img.quantize(colors=max(8, k * 2), method=Image.MEDIANCUT)
        palette = q.getpalette()
        color_counts = q.getcolors()
        if not palette or not color_counts:
            return []
        # Sort by frequency
        color_counts.sort(key=lambda x: x[0], reverse=True)
        color_names: List[str] = []
        for count, color_index in color_counts[: k * 2]:
            base = color_index * 3
            rgb = (palette[base], palette[base + 1], palette[base + 2])
            name = _nearest_color_name(rgb)
            if name not in color_names:
                color_names.append(name)
            if len(color_names) >= k:
                break
        return color_names
    except Exception:
        return []


def _build_title(tokens: List[str], lang: str) -> str:
    if not tokens:
        return "Untitled" if lang.startswith("en") else "未命名"
    if lang.startswith("en"):
        return " ".join([t.capitalize() for t in tokens[:10]])
    # Chinese or others: join without capitalization
    return " ".join(tokens[:10])


def _build_description(tokens: List[str], colors: List[str], lang: str) -> str:
    core = ", ".join(tokens[:8]) if tokens else ("image" if lang.startswith("en") else "图片")
    color_part = ", ".join(colors) if colors else ""
    if lang.startswith("en"):
        if color_part:
            return f"High-quality stock photo featuring {core}, with {color_part} tones. Ideal for editorial and commercial use."
        return f"High-quality stock photo featuring {core}. Ideal for editorial and commercial use."
    else:
        if color_part:
            return f"高质量图库照片，主体为：{core}，色调包含：{color_part}。适用于商业与编辑用途。"
        return f"高质量图库照片，主体为：{core}。适用于商业与编辑用途。"


def _limit_keywords(keywords: List[str], limit: int) -> List[str]:
    final: List[str] = []
    for kw in keywords:
        kw_norm = kw.strip().lower()
        if not kw_norm or kw_norm in final:
            continue
        final.append(kw_norm)
        if len(final) >= limit:
            break
    return final


def generate_metadata(
    image_path: str,
    lang: str = "en",
    provider: str = "heuristic",
    max_keywords: int = 49,
) -> Dict[str, object]:
    """
    Generate keywords, title and description for an image.

    provider: 'heuristic' or 'openai'
    lang: 'en' or 'zh' etc.
    max_keywords: cap keyword list length for specific platforms
    """
    if provider == "openai" and OpenAI is not None:
        try:
            md = _generate_with_openai(image_path, lang=lang, max_keywords=max_keywords)
            if md:
                return md
        except Exception:
            pass

    # Heuristic fallback
    tokens = _tokenize_filename(image_path)
    colors = _dominant_colors(image_path)
    # Construct candidate keywords
    keywords = tokens + colors
    # Add generic stock tags
    if lang.startswith("en"):
        keywords += ["stock photo", "high resolution", "background", "nature", "abstract"]
    else:
        keywords += ["图库", "高分辨率", "背景", "自然", "抽象"]

    keywords = _limit_keywords(keywords, max_keywords)
    title = _build_title(tokens or colors, lang)
    description = _build_description(tokens or colors, colors, lang)

    return {
        "filename": os.path.basename(image_path),
        "title": title,
        "description": description,
        "keywords": keywords,
        "language": lang,
        "source_path": image_path,
    }


def _generate_with_openai(image_path: str, lang: str, max_keywords: int) -> Optional[Dict[str, object]]:
    if OpenAI is None:
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    client = OpenAI(api_key=api_key)
    # For small images, inline base64; otherwise, we only send text prompt (no vision) as a fallback
    try:
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        b64 = ""

    target_lang = "English" if lang.startswith("en") else "Chinese"
    prompt = (
        "You are a stock photography metadata assistant. Generate an SEO-friendly title, "
        "a concise commercial-ready description, and a list of highly relevant single or two-word keywords. "
        f"Return no more than {max_keywords} keywords. Respond in {target_lang}. "
        "Output JSON with keys: title, description, keywords (array)."
    )

    content = []
    if b64:
        content.append({"type": "input_text", "text": prompt})
        content.append({"type": "input_image", "image_data": b64})
    else:
        content.append({"type": "input_text", "text": prompt})

    # Use responses API if available; fall back to chat.completions-like
    try:
        # This block assumes new Responses API; adapt if different openai lib version
        resp = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=content,
        )
        text = resp.output_text
    except Exception:
        # Legacy
        try:
            chat = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            text = chat.choices[0].message.content
        except Exception:
            return None

    # Parse JSON heuristically
    try:
        import json
        data = json.loads(text)  # type: ignore
        kws = [str(k).strip() for k in data.get("keywords", [])]
        kws = _limit_keywords(kws, max_keywords)
        return {
            "filename": os.path.basename(image_path),
            "title": str(data.get("title", "Untitled")),
            "description": str(data.get("description", "")),
            "keywords": kws,
            "language": lang,
            "source_path": image_path,
        }
    except Exception:
        return None