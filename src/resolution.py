"""Aspect-ratio / megapixel resolution helper.

Ported from ComfyUI's built-in ``ResolutionSelector`` node
(comfy_extras/nodes_resolution.py), which computes width and height from an
aspect ratio and a target pixel budget instead of making you do the arithmetic.

Latent models require each dimension to be a multiple of their downsampling
factor (8 in general, 16 for the Qwen-Image VAE, 64 for Flux), so the result is
rounded to a configurable multiple. Getting this wrong is what produces
"latent shape not divisible by 8" style failures.
"""

import math

CUSTOM = "Custom"

# (label, width_ratio, height_ratio)
ASPECT_RATIOS = [
    ("1:1 (Square)", 1, 1),
    ("2:3 (Portrait Photo)", 2, 3),
    ("3:2 (Photo)", 3, 2),
    ("3:4 (Portrait Standard)", 3, 4),
    ("4:3 (Standard)", 4, 3),
    ("9:16 (Portrait Widescreen)", 9, 16),
    ("16:9 (Widescreen)", 16, 9),
    ("21:9 (Ultrawide)", 21, 9),
]

ASPECT_RATIO_LABELS = [label for label, _, _ in ASPECT_RATIOS] + [CUSTOM]

_RATIO_MAP = {label: (wr, hr) for label, wr, hr in ASPECT_RATIOS}

# Presets sized for the model families this GUI drives.
# (label, width, height)
RESOLUTION_PRESETS = [
    ("SD 1.5 (512)", 512, 512),
    ("SDXL 1:1", 1024, 1024),
    ("SDXL 2:3", 832, 1216),
    ("SDXL 3:2", 1216, 832),
    ("SDXL 16:9", 1344, 768),
    ("Flux 1:1", 1024, 1024),
    ("Flux 16:9", 1344, 768),
    ("Flux 2:1", 1408, 704),
]

PRESET_LABELS = [label for label, _, _ in RESOLUTION_PRESETS]
_PRESET_MAP = {label: (w, h) for label, w, h in RESOLUTION_PRESETS}


def round_to_multiple(value, multiple):
    """Rounds value to the nearest multiple, never returning less than one step."""
    if multiple < 1:
        multiple = 1
    rounded = round(value / multiple) * multiple
    return max(multiple, rounded)


def resolution_from_megapixels(aspect_label, megapixels, multiple=8):
    """Returns (width, height) for a preset aspect ratio and pixel budget.

    area = megapixels * 1024 * 1024, then scaled so that
    width * height lands on that area at the requested aspect ratio.
    """
    if aspect_label not in _RATIO_MAP:
        raise ValueError(f"unknown aspect ratio: {aspect_label!r}")

    w_ratio, h_ratio = _RATIO_MAP[aspect_label]
    try:
        megapixels = float(megapixels)
    except (TypeError, ValueError):
        megapixels = 1.0
    if megapixels <= 0:
        megapixels = 1.0

    total_pixels = megapixels * 1024 * 1024
    scale = math.sqrt(total_pixels / (w_ratio * h_ratio))

    width = round_to_multiple(w_ratio * scale, multiple)
    height = round_to_multiple(h_ratio * scale, multiple)
    return width, height


def resolution_from_preset(preset_label):
    """Returns the fixed (width, height) for a named model preset."""
    if preset_label not in _PRESET_MAP:
        raise ValueError(f"unknown preset: {preset_label!r}")
    return _PRESET_MAP[preset_label]


def megapixels_of(width, height):
    """Actual megapixels of a width/height pair, for the readout."""
    try:
        return (float(width) * float(height)) / (1024 * 1024)
    except (TypeError, ValueError):
        return 0.0


def is_valid_resolution(width, height, multiple=8):
    """True when both dimensions are positive multiples, as latents require."""
    try:
        width = int(width)
        height = int(height)
    except (TypeError, ValueError):
        return False
    if width <= 0 or height <= 0 or multiple < 1:
        return False
    return width % multiple == 0 and height % multiple == 0
