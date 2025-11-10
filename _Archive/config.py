import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PREVIEW_DIR = os.path.join(BASE_DIR, "previews")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

ALLOWED_PSD_EXT = {"psd", "psb"}
ALLOWED_FONT_EXT = {"ttf", "otf"}
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB

for d in (UPLOAD_DIR, PREVIEW_DIR, OUTPUT_DIR, FONTS_DIR):
    os.makedirs(d, exist_ok=True)
