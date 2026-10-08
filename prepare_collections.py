"""Prepare News or Pushback source pages for the website archive.

Usage:
    python prepare_collections.py news
    python prepare_collections.py pushback

Put original scans in assets/documents/<collection>/raw using filenames such as:
    A - Article title_Page_1.png
    A - Article title_Page_2.png
    B - Another article.pdf

Optional titles and dates are read from each collection's metadata.json.
PDF support requires PyMuPDF: python -m pip install pymupdf
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
WEB_MAX_SIZE = 2200
THUMB_MAX_SIZE = 600
WEB_QUALITY = 88
THUMB_QUALITY = 78
ALLOWED_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
NAME_RE = re.compile(r"^([A-Z])\s*[-_]\s*(.+)$", flags=re.IGNORECASE)
PAGE_RE = re.compile(r"(?:[_\s-]+Page[_\s-]*)(\d+)$", flags=re.IGNORECASE)


def parse_source(path):
    match = NAME_RE.match(path.stem)
    if not match:
        raise ValueError(f"Source filename must begin with a group letter and hyphen: {path.name}")
    group, title = match.group(1).upper(), match.group(2).strip()
    page_match = PAGE_RE.search(title)
    page = int(page_match.group(1)) if page_match else None
    title = PAGE_RE.sub("", title).strip()
    return group, title, page


def slugify(value):
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    if not slug:
        raise ValueError(f"Cannot create a filename from: {value}")
    return slug[:90].rstrip("-")


def rgb_copy(image):
    image = ImageOps.exif_transpose(image)
    if image.mode == "RGB":
        return image.copy()
    rgba = image.convert("RGBA")
    rgb = Image.new("RGB", rgba.size, "white")
    rgb.paste(rgba, mask=rgba.getchannel("A"))
    return rgb


def resized(image, max_size):
    result = image.copy()
    result.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return result


def pdf_pages(path):
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PDF detected. Install support with: python -m pip install pymupdf") from exc
    with pymupdf.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0), alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            yield page_number, image


def main():
    parser = argparse.ArgumentParser(description="Prepare one ACPT document collection")
    parser.add_argument("collection", choices=["news", "pushback"])
    args = parser.parse_args()

    base = ROOT / "assets" / "documents" / args.collection
    raw_dir, web_dir, thumb_dir = [base / name for name in ("raw", "web", "thumbs")]
    for directory in (raw_dir, web_dir, thumb_dir):
        directory.mkdir(parents=True, exist_ok=True)

    metadata_path = base / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {"groups": {}}
    metadata_groups = metadata.get("groups", {})
    source_files = sorted([p for p in raw_dir.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_TYPES], key=lambda p: p.name.lower())
    if not source_files:
        print(f"No documents found in {raw_dir}. Existing manifest left untouched.")
        return

    pending = []
    for source in source_files:
        group, inferred_title, supplied_page = parse_source(source)
        if source.suffix.lower() == ".pdf":
            if supplied_page is not None:
                raise ValueError(f"PDF filename must not include a page number: {source.name}")
            for page_number, image in pdf_pages(source):
                pending.append((group, inferred_title, page_number, source, image))
        else:
            with Image.open(source) as opened:
                pending.append((group, inferred_title, supplied_page, source, opened.copy()))

    pending.sort(key=lambda entry: (entry[0], entry[2] or 0, entry[3].name.lower()))
    seen_names = set()
    manifest = []
    for group, inferred_title, page_number, source, original in pending:
        group_info = metadata_groups.get(group, {})
        title = group_info.get("title") or inferred_title
        date = group_info.get("date") or ""
        filename_base = f"{group.lower()}-{slugify(inferred_title)}"
        if page_number is not None:
            filename_base += f"-page-{page_number:02d}"
        filename = filename_base + ".webp"
        if filename in seen_names:
            raise ValueError(f"Duplicate output filename: {filename}. Check group names and page numbers.")
        seen_names.add(filename)

        original = rgb_copy(original)
        width, height = original.size
        web_path = web_dir / filename
        thumb_path = thumb_dir / filename
        resized(original, WEB_MAX_SIZE).save(web_path, "WEBP", quality=WEB_QUALITY, method=6)
        resized(original, THUMB_MAX_SIZE).save(thumb_path, "WEBP", quality=THUMB_QUALITY, method=6)
        manifest.append({
            "group": group,
            "group_name": slugify(inferred_title),
            "title": title,
            "date": date,
            "page": page_number,
            "original_filename": source.name,
            "web_filename": filename,
            "thumbnail_filename": filename,
            "original_width": width,
            "original_height": height,
            "original_bytes": source.stat().st_size,
            "web_bytes": web_path.stat().st_size,
            "thumbnail_bytes": thumb_path.stat().st_size,
        })
        print(f"{source.name} -> {filename}")

    manifest_path = base / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Prepared {len(manifest)} document images for {args.collection}.")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
