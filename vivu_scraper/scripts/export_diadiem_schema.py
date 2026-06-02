from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "vivu_backend"
OUTPUT_DIR = REPO_ROOT / "vivu_scraper" / "outputs"
JSON_OUTPUT = OUTPUT_DIR / "diadiem_schema.json"
MD_OUTPUT = OUTPUT_DIR / "diadiem_schema.md"


def setup_django() -> None:
    import sys

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")

    import django

    django.setup()


def field_to_dict(field: Any) -> Dict[str, Any]:
    rel_model = None
    if getattr(field, "remote_field", None) and getattr(field.remote_field, "model", None):
        rel_model = field.remote_field.model.__name__

    choices = None
    if getattr(field, "choices", None):
        choices = [{"value": value, "label": label} for value, label in field.choices]

    return {
        "name": field.name,
        "db_column": field.db_column or field.name,
        "type": field.get_internal_type(),
        "null": field.null,
        "blank": getattr(field, "blank", False),
        "primary_key": field.primary_key,
        "unique": field.unique,
        "indexed": getattr(field, "db_index", False),
        "max_length": getattr(field, "max_length", None),
        "default": None if field.default is None or callable(field.default) else field.default,
        "choices": choices,
        "related_model": rel_model,
    }


def export_schema() -> Dict[str, Any]:
    setup_django()

    from apps.places.models import DiaDiem

    fields: List[Dict[str, Any]] = [field_to_dict(field) for field in DiaDiem._meta.fields]
    indexes = []
    for index in DiaDiem._meta.indexes:
        indexes.append(
            {
                "name": getattr(index, "name", ""),
                "fields": list(index.fields),
            }
        )

    unique_together = list(getattr(DiaDiem._meta, "unique_together", []))

    payload = {
        "model": "DiaDiem",
        "db_table": DiaDiem._meta.db_table,
        "ordering": list(DiaDiem._meta.ordering),
        "unique_together": unique_together,
        "fields": fields,
        "indexes": indexes,
    }
    return payload


def write_outputs(payload: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Schema bang DIADIEM",
        "",
        f"- Model: `{payload['model']}`",
        f"- Table: `{payload['db_table']}`",
        f"- Ordering: `{payload['ordering']}`",
        "",
        "| Truong | Cot DB | Kieu | Null | Blank | PK | Unique | Index | Quan he |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for field in payload["fields"]:
        lines.append(
            "| {name} | {db_column} | {type} | {null} | {blank} | {primary_key} | {unique} | {indexed} | {related_model} |".format(
                **{
                    **field,
                    "related_model": field["related_model"] or "",
                }
            )
        )

    if payload["indexes"]:
        lines.extend(["", "## Indexes", ""])
        for index in payload["indexes"]:
            lines.append(f"- `{index['name']}`: {', '.join(index['fields'])}")

    MD_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = export_schema()
    write_outputs(payload)
    print(f"Da xuat schema JSON: {JSON_OUTPUT}")
    print(f"Da xuat schema Markdown: {MD_OUTPUT}")
    print(f"So truong: {len(payload['fields'])}")


if __name__ == "__main__":
    main()
