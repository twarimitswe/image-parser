"""Image loading and the cleanup that makes scanned forms readable to OCR."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Union

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

from .exceptions import ImageLoadError

ImageSource = Union[str, Path, bytes, Image.Image]

MIN_OCR_WIDTH = 1600
"""Tesseract loses accuracy on A4 scans narrower than roughly 200 DPI."""


def load(source: ImageSource) -> Image.Image:
    """Open ``source`` -- a path, raw bytes or an existing image -- for parsing."""
    if isinstance(source, Image.Image):
        return source
    try:
        image = Image.open(io.BytesIO(source) if isinstance(source, bytes) else source)
        image.load()
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise ImageLoadError(f"could not decode image: {exc}") from exc
    return ImageOps.exif_transpose(image)


def prepare(
    image: Image.Image, *, min_width: int = MIN_OCR_WIDTH, binarize: bool = True
) -> Image.Image:
    """Return a grayscale, upscaled, contrast-normalized copy of ``image``."""
    prepared = ImageOps.grayscale(image)
    if prepared.width < min_width:
        height = round(prepared.height * min_width / prepared.width)
        prepared = prepared.resize((min_width, height), Image.LANCZOS)
    prepared = ImageOps.autocontrast(prepared).filter(ImageFilter.UnsharpMask(radius=1.5))
    if binarize:
        threshold = otsu_threshold(prepared)
        prepared = prepared.point(lambda level: 255 if level > threshold else 0)
    return prepared


def otsu_threshold(image: Image.Image) -> int:
    """Pick the gray level that best splits ink from paper (Otsu's method)."""
    histogram = image.histogram()[:256]
    total = sum(histogram)
    total_weighted = sum(level * count for level, count in enumerate(histogram))
    best_level, best_variance, background, background_weighted = 128, -1.0, 0, 0
    for level, count in enumerate(histogram):
        background += count
        background_weighted += level * count
        foreground = total - background
        if background == 0 or foreground == 0:
            continue
        mean_gap = background_weighted / background - (total_weighted - background_weighted) / foreground
        variance = background * foreground * mean_gap**2
        if variance > best_variance:
            best_level, best_variance = level, variance
    return best_level
