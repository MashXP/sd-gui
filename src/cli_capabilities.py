"""Discovers which sampler, scheduler and cache options the sd-cli binary supports.

The option lists are parsed out of ``sd-cli --help`` rather than hardcoded, so
the GUI always offers exactly what the installed binary accepts. sd-cli grows
new options over time -- for example ``flux`` is required by Qwen-Image-2.1 and
Flux, and a hardcoded list can silently omit it.
"""

import os
import re
import subprocess

# Used when the binary is missing or its help text cannot be parsed, so the
# comboboxes are never empty.
FALLBACK_SAMPLING_METHODS = [
    "euler", "euler_a", "heun", "dpm2", "dpm++2s_a", "dpm++2m",
    "dpm++2mv2", "ipndm", "ipndm_v", "lcm", "ddim_trailing", "tcd",
    "res_multistep", "res_2s", "er_sde", "euler_cfg_pp", "euler_a_cfg_pp",
    "euler_ge", "dpm++2m_sde", "dpm++2m_sde_bt", "lms",
]

FALLBACK_SCHEDULERS = [
    "discrete", "karras", "exponential", "ays", "gits", "sgm_uniform", "simple",
    "smoothstep", "kl_optimal", "lcm", "bong_tangent", "ltx2", "logit_normal",
    "flux2", "flux", "beta", "llada_image",
]

FALLBACK_CACHE_MODES = [
    "easycache", "ucache", "dbcache", "taylorseer", "cache-dit", "spectrum",
]

_HELP_TIMEOUT = 10


def read_cli_help(binary_path):
    """Runs the binary with --help, returning its output, or None on failure."""
    if not binary_path or not os.path.exists(binary_path):
        return None
    try:
        result = subprocess.run(
            [binary_path, "--help"],
            capture_output=True,
            text=True,
            timeout=_HELP_TIMEOUT,
        )
    except Exception:
        return None
    output = (result.stdout or "") + (result.stderr or "")
    return output if output.strip() else None


def _entry_text(help_text, flag):
    """Returns the full help entry for a flag, with continuations joined.

    sd-cli wraps option lists over several lines. Matching is anchored to the
    start of an entry so that, for example, --sampling-method does not pick up
    --high-noise-sampling-method, and collection stops at the next flag so a
    neighbouring option's text is never swept in.
    """
    if not help_text:
        return ""

    # An entry starts at a line beginning with the flag, optionally preceded by
    # a short form such as "-s, ".
    entry_re = re.compile(r"^\s+(?:-\w,\s*)?" + re.escape(flag) + r"(?=\s|$)")
    next_flag_re = re.compile(r"^\s+(?:-\w,\s*)?--[a-zA-Z0-9]")

    lines = help_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if entry_re.match(line):
            start = i
            break
    if start is None:
        return ""

    body = []
    for line in lines[start:]:
        if body and next_flag_re.match(line):
            break
        body.append(line)
    return " ".join(body)


def parse_enum_options(help_text, flag):
    """Extracts the ``one of [...]`` values documented for a CLI flag.

    Used for --sampling-method and --scheduler, whose lists end with a
    bracketed comma-separated enumeration.
    """
    match = re.search(r"one of \[([^\]]*)\]", _entry_text(help_text, flag), re.IGNORECASE)
    if not match:
        return []
    # Options are comma separated and may themselves contain '+' (dpm++2m).
    return [opt.strip() for opt in match.group(1).split(",") if opt.strip()]


def parse_quoted_options(help_text, flag):
    """Extracts single-quoted names documented for a CLI flag.

    Used for --cache-mode, which is not documented as a bracketed enumeration.
    Its help reads "'dbcache'/'taylorseer'/'cache-dit' (DiT block-level)",
    so each quoted group is split on '/' as well as matched individually.
    """
    entry = _entry_text(help_text, flag)
    if not entry:
        return []

    options = []
    for group in re.findall(r"'([^']+)'", entry):
        for opt in group.split("/"):
            opt = opt.strip()
            if opt:
                options.append(opt)
    return options


def discover(binary_path):
    """Returns the samplers, schedulers and cache modes the binary advertises.

    Falls back to the built-in lists when help cannot be read, so a missing
    binary degrades the options rather than breaking the UI.
    """
    help_text = read_cli_help(binary_path)

    sampling_methods = parse_enum_options(help_text, "--sampling-method")
    schedulers = parse_enum_options(help_text, "--scheduler")
    cache_modes = parse_quoted_options(help_text, "--cache-mode")

    return {
        "sampling_methods": sampling_methods or list(FALLBACK_SAMPLING_METHODS),
        "schedulers": schedulers or list(FALLBACK_SCHEDULERS),
        "cache_modes": cache_modes or list(FALLBACK_CACHE_MODES),
        "discovered": bool(sampling_methods and schedulers and cache_modes),
    }
