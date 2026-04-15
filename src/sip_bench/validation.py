from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_schema(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_data_file(
    *,
    data_path: str | Path,
    schema_path: str | Path,
    input_format: str | None = None,
    max_errors: int = 20,
) -> dict[str, Any]:
    data_path = Path(data_path)
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    format_name = input_format or _infer_format(data_path)

    if format_name == "jsonl":
        records = _load_jsonl(data_path)
    elif format_name == "json":
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else [payload]
    else:
        raise ValueError(f"Unsupported input format: {format_name}")

    errors: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        for error in validator.iter_errors(record):
            errors.append(
                {
                    "record_index": index,
                    "path": _error_path(error.absolute_path),
                    "message": error.message,
                }
            )
            if len(errors) >= max_errors:
                break
        if len(errors) >= max_errors:
            break

    return {
        "data_path": str(data_path),
        "schema_path": str(schema_path),
        "input_format": format_name,
        "records_checked": len(records),
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number} in {path}") from exc
    return records


def _infer_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".json":
        return "json"
    raise ValueError(f"Cannot infer input format from suffix: {suffix}")


def _error_path(path_parts: Any) -> str:
    parts = [str(part) for part in path_parts]
    return ".".join(parts) if parts else "<root>"
