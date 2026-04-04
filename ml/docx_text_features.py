# простые числовые фичи по строке текста docx, без эмбеддингов
from __future__ import annotations

import math
import re
import string
from typing import Dict, List

import numpy as np

# пунктуация лат + то что часто в рус/англ
_PUNCT_EXTRA = "«»—–…„“”"
_PUNCT_SET = set(string.punctuation + _PUNCT_EXTRA)

WORD_RE = re.compile(r"\S+", re.UNICODE)


DOCX_TEXT_FEATURE_NAMES: List[str] = [
    "digit_char_ratio",
    "log1p_char_count",
    "log1p_nonempty_line_count",
    "log1p_word_count",
    "log1p_longest_word",
    "mean_word_length",
    "punctuation_ratio",
    "unique_word_ratio",
    "upper_alpha_ratio",
]


def extract_docx_text_features(text: str) -> Dict[str, float]:
    # из сырого текста; пустой → нули
    empty = {name: 0.0 for name in DOCX_TEXT_FEATURE_NAMES}
    if not text or not text.strip():
        return empty

    t = text.strip()
    n_chars = len(t)
    if n_chars == 0:
        return empty

    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    n_lines = max(len(lines), 1)

    words = WORD_RE.findall(t)
    n_words = len(words)
    if n_words == 0:
        return {
            **empty,
            "log1p_char_count": float(math.log1p(n_chars)),
            "log1p_nonempty_line_count": float(math.log1p(len(lines))),
        }

    lower_words = [w.lower() for w in words]
    unique_ratio = len(set(lower_words)) / float(n_words)
    mean_wlen = sum(len(w) for w in words) / float(n_words)
    longest = min(max(len(w) for w in words), 500)

    digits = sum(1 for c in t if c.isdigit())
    punct = sum(1 for c in t if c in _PUNCT_SET or (not c.isalnum() and not c.isspace()))
    alpha = [c for c in t if c.isalpha()]
    upper_r = (
        sum(1 for c in alpha if c.isupper()) / float(len(alpha)) if alpha else 0.0
    )

    return {
        "digit_char_ratio": min(1.0, digits / float(n_chars)),
        "log1p_char_count": float(math.log1p(n_chars)),
        "log1p_nonempty_line_count": float(math.log1p(len(lines))),
        "log1p_word_count": float(math.log1p(n_words)),
        "log1p_longest_word": float(math.log1p(longest)),
        "mean_word_length": float(min(mean_wlen, 100.0)),
        "punctuation_ratio": min(1.0, punct / float(n_chars)),
        "unique_word_ratio": float(min(unique_ratio, 1.0)),
        "upper_alpha_ratio": float(min(max(upper_r, 0.0), 1.0)),
    }


def vectorize_docx_text_features(
    combined: Dict[str, float],
    names: List[str] | None = None,
) -> np.ndarray:
    names = names or DOCX_TEXT_FEATURE_NAMES
    return np.array([combined.get(n, 0.0) for n in names], dtype=np.float64)
