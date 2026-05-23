"""
Utilities de resolve tinh thanh Viet Nam va filter ket qua theo ground truth.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable, List, Optional, Sequence, Tuple


_STOPWORDS = {"thanh", "pho", "thanhpho", "tp", "tinh"}
_ALIAS_MAP = {
    "ho chi minh": ["tp hcm", "tphcm", "tp.hcm", "sai gon", "saigon", "hcm"],
    "ba ria vung tau": ["br vt", "br-vt", "vung tau", "ba ria"],
    "thua thien hue": ["hue", "tp hue", "thanh pho hue"],
    "dak lak": ["daklak", "dak lac", "buon ma thuot"],
    "dak nong": ["daknong", "dak nong", "gia nghia"],
    "can tho": ["tp can tho", "thanh pho can tho"],
    "da nang": ["tp da nang", "thanh pho da nang"],
    "ha noi": ["thu do", "tp ha noi", "thanh pho ha noi"],
    "hai phong": ["tp hai phong", "thanh pho hai phong"],
    "khanh hoa": ["nha trang"],
    "lam dong": ["da lat", "dalat"],
    "quang nam": ["hoi an", "my son", "thanh dia my son"],
    "kien giang": ["phu quoc"],
    "quang ninh": ["ha long", "halong"],
    "binh dinh": ["quy nhon"],
    "dong thap": ["cao lanh"],
    "an giang": ["long xuyen", "chau doc"],
    "gia lai": ["pleiku"],
}


def normalize_location_text(value: str) -> str:
    """Normalize text de so khop substring/token theo tieng Viet."""
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def tokenize_location_text(value: str) -> List[str]:
    normalized = normalize_location_text(value)
    if not normalized:
        return []
    return [token for token in normalized.split() if token and token not in _STOPWORDS]


def get_province_aliases(province_name: str) -> List[str]:
    normalized_name = normalize_location_text(province_name)
    aliases = {normalized_name}
    tokens = tokenize_location_text(province_name)
    if tokens:
        aliases.add(" ".join(tokens))
    aliases.update(_ALIAS_MAP.get(normalized_name, []))
    return [alias for alias in aliases if alias]


def score_province_match(query: str, province_name: str) -> float:
    normalized_query = normalize_location_text(query)
    if not normalized_query:
        return 0.0

    province_aliases = get_province_aliases(province_name)
    best = 0.0
    query_tokens = set(tokenize_location_text(query))

    for alias in province_aliases:
        alias_normalized = normalize_location_text(alias)
        alias_tokens = set(tokenize_location_text(alias))
        if not alias_tokens:
            continue

        if alias_normalized in normalized_query:
            # Exact substring match duoc uu tien cao nhat.
            score = 1.0 + (len(alias_tokens) * 0.05)
        else:
            common = query_tokens & alias_tokens
            if not common:
                continue
            union = query_tokens | alias_tokens
            score = len(common) / max(len(union), 1)
            if common == alias_tokens:
                score += 0.2

        best = max(best, score)

    return best


def resolve_best_province(
    query: str,
    provinces: Sequence[Tuple[int, str]],
    minimum_score: float = 0.45,
) -> Optional[Tuple[int, str, float]]:
    """Tra ve (maTinhThanh, tenTinhThanh, score) tot nhat."""
    best_match: Optional[Tuple[int, str, float]] = None
    for province_id, province_name in provinces:
        score = score_province_match(query, province_name)
        if score < minimum_score:
            continue
        if best_match is None or score > best_match[2]:
            best_match = (province_id, province_name, score)
    return best_match


def text_matches_province(
    text_candidates: Iterable[Optional[str]],
    province_name: str,
    minimum_score: float = 0.45,
) -> bool:
    for candidate in text_candidates:
        if not candidate:
            continue
        if score_province_match(str(candidate), province_name) >= minimum_score:
            return True
    return False
