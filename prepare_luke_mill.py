from pathlib import Path
from PIL import Image
import json
import re

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

ROOT = Path(__file__).parent

RAW_DIR = ROOT / "assets" / "documents" / "luke-mill" / "raw"
WEB_DIR = ROOT / "assets" / "documents" / "luke-mill" / "web"
THUMB_DIR = ROOT / "assets" / "documents" / "luke-mill" / "thumbs"

WEB_DIR.mkdir(parents=True, exist_ok=True)
THUMB_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

# Maximum long edge for the image a visitor opens.
WEB_MAX_SIZE = 2200

# Maximum long edge for thumbnails used on the webpage.
THUMB_MAX_SIZE = 600

WEB_QUALITY = 88
THUMB_QUALITY = 78


# ------------------------------------------------------------
# CLEAN FILENAMES
# ------------------------------------------------------------

GROUP_NAMES = {
    "A": "mou-port-river-west-2024-08-07",
    "B": "property-purchase-example",
    "C": "deed-west-virginia-property",
    "D": "bocc-agenda-2025-07-10",
    "E": "closed-session-notice",
    "F": "bocc-agenda-2024-08-08",
    "G": "bocc-agenda-2024-08-22",
    "H": "port-river-west-agreement-2025-07-10",
    "I": "bocc-agenda-2025-07-10-secondary",
    "J": "bocc-agenda-packet-signed-documents-2025-07-10",
}


def get_group(filename: str) -> str:
    match = re.match(r"^([A-J])", filename.strip(), re.IGNORECASE)

    if not match:
        raise ValueError(f"Could not determine group for: {filename}")

    return match.group(1).upper()


def get_page_number(filename: str):
    patterns = [
        r"_Page_(\d+)",
        r"_Page(\d+)",
        r"Page_(\d+)",
        r"Page(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def make_clean_name(path: Path):
    group = get_group(path.name)
    slug = GROUP_NAMES[group]
    page = get_page_number(path.name)

    if page is not None:
        return f"{group.lower()}-{slug}-page-{page:02d}.webp"

    return f"{group.lower()}-{slug}.webp"


# ------------------------------------------------------------
# IMAGE PROCESSING
# ------------------------------------------------------------

def resize_copy(image: Image.Image, max_size: int):
    img = image.copy()

    width, height = img.size

    scale = min(
        1,
        max_size / max(width, height)
    )

    if scale < 1:
        new_width = round(width * scale)
        new_height = round(height * scale)

        img = img.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )

    return img


def make_rgb(image: Image.Image):
    """
    WebP supports alpha, but these are document images and we don't
    need transparency. Flattening against white keeps output predictable.
    """

    if image.mode == "RGB":
        return image

    if image.mode in ("RGBA", "LA"):
        background = Image.new(
            "RGB",
            image.size,
            "white"
        )

        if image.mode == "RGBA":
            background.paste(image, mask=image.getchannel("A"))
        else:
            background.paste(image.convert("RGBA"), mask=image.getchannel("A"))

        return background

    return image.convert("RGB")


# ------------------------------------------------------------
# PROCESS
# ------------------------------------------------------------

source_files = sorted(
    [
        path
        for path in RAW_DIR.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ],
    key=lambda p: (
        get_group(p.name),
        get_page_number(p.name) or 0,
        p.name
    )
)

print()
print(f"Found {len(source_files)} source images.")
print()

manifest = []

for number, source_path in enumerate(source_files, start=1):

    clean_name = make_clean_name(source_path)

    web_path = WEB_DIR / clean_name
    thumb_path = THUMB_DIR / clean_name

    with Image.open(source_path) as original:

        original_width, original_height = original.size

        original = make_rgb(original)

        # Full web image
        web_image = resize_copy(
            original,
            WEB_MAX_SIZE
        )

        web_image.save(
            web_path,
            "WEBP",
            quality=WEB_QUALITY,
            method=6
        )

        # Thumbnail
        thumb_image = resize_copy(
            original,
            THUMB_MAX_SIZE
        )

        thumb_image.save(
            thumb_path,
            "WEBP",
            quality=THUMB_QUALITY,
            method=6
        )

    group = get_group(source_path.name)
    page = get_page_number(source_path.name)

    original_size = source_path.stat().st_size
    web_size = web_path.stat().st_size
    thumb_size = thumb_path.stat().st_size

    manifest.append(
        {
            "group": group,
            "group_name": GROUP_NAMES[group],
            "page": page,
            "original_filename": source_path.name,
            "web_filename": clean_name,
            "thumbnail_filename": clean_name,
            "original_width": original_width,
            "original_height": original_height,
            "original_bytes": original_size,
            "web_bytes": web_size,
            "thumbnail_bytes": thumb_size,
        }
    )

    print(
        f"[{number:02d}/{len(source_files):02d}] "
        f"{source_path.name}"
    )

    print(
        f"      -> {clean_name}"
    )

    print(
        f"      {original_size / 1024 / 1024:.2f} MB "
        f"-> {web_size / 1024 / 1024:.2f} MB "
        f"(thumb {thumb_size / 1024:.0f} KB)"
    )

    print()


# ------------------------------------------------------------
# MANIFEST
# ------------------------------------------------------------

manifest_path = (
    ROOT
    / "assets"
    / "documents"
    / "luke-mill"
    / "manifest.json"
)

with manifest_path.open("w", encoding="utf-8") as f:
    json.dump(
        manifest,
        f,
        indent=2
    )


# ------------------------------------------------------------
# TOTALS
# ------------------------------------------------------------

raw_total = sum(item["original_bytes"] for item in manifest)
web_total = sum(item["web_bytes"] for item in manifest)
thumb_total = sum(item["thumbnail_bytes"] for item in manifest)

print("=" * 70)
print("DONE")
print("=" * 70)

print(
    f"Original images:   {raw_total / 1024 / 1024:.2f} MB"
)

print(
    f"Web images:        {web_total / 1024 / 1024:.2f} MB"
)

print(
    f"Thumbnails:        {thumb_total / 1024 / 1024:.2f} MB"
)

print()
print(f"Web files:   {WEB_DIR}")
print(f"Thumbnails:  {THUMB_DIR}")
print(f"Manifest:    {manifest_path}")