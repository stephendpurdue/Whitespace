"""Validate records against shared JSON schemas."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator


@lru_cache
def _load_validator(schema_name: str, schemas_dir: str) -> Draft202012Validator:
    schema_path = Path(schemas_dir) / schema_name
    schema = json.loads(schema_path.read_text())
    return Draft202012Validator(schema)


def validate_record(record: dict[str, Any], schema_name: str, schemas_dir: Path) -> None:
    validator = _load_validator(schema_name, str(schemas_dir))
    validator.validate(record)
