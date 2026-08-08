"""Authoritative parsing and validation. Development/CI only.

Every YAML read and every schema validation in this repository goes through this
module, so there is exactly one place where the authoritative implementations are
selected:

    YAML        -> yaml.safe_load                (PyYAML)
    JSON Schema -> jsonschema, validator class chosen from each schema's own $schema

`safe_load` rather than `load`: schema and metadata files are data, and a full-power
loader would let a crafted file construct Python objects.

The validator class is resolved from the `$schema` each file declares rather than being
hard-coded, so a schema that later moves to a different draft is validated as the draft
it claims to be instead of silently under a different one.
"""

from __future__ import annotations

import functools
import json
import pathlib

import jsonschema
import yaml

from _common import FrontmatterError, split_frontmatter


class SchemaError(Exception):
    """The schema file itself is invalid (not the instance)."""


def load_yaml(path) -> object:
    """Parse a YAML file with PyYAML. Raises yaml.YAMLError on malformed input."""
    return yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))


def load_yaml_text(text: str) -> object:
    return yaml.safe_load(text)


def load_frontmatter(path) -> tuple[object, str]:
    """Return (parsed frontmatter, body) for a Markdown file.

    Boundary extraction is ours; parsing is PyYAML's. A malformed frontmatter block
    therefore fails with a real yaml.YAMLError describing the actual YAML problem,
    not with a guess from a subset parser.
    """
    text = pathlib.Path(path).read_text(encoding="utf-8")
    raw, body = split_frontmatter(text)
    return yaml.safe_load(raw), body


@functools.lru_cache(maxsize=None)
def load_schema(path_str: str) -> dict:
    schema = json.loads(pathlib.Path(path_str).read_text(encoding="utf-8"))
    if "$schema" not in schema:
        raise SchemaError(f"{path_str}: schema does not declare $schema")
    if "$id" not in schema:
        raise SchemaError(f"{path_str}: schema does not declare a stable $id")
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    return schema


def validator_for(schema: dict):
    """Return a jsonschema validator matching the draft the schema declares."""
    return jsonschema.validators.validator_for(schema)(schema)


def validate(instance, schema: dict) -> list[str]:
    """Validate an instance, returning sorted human-readable error strings.

    Empty list means valid. Errors are sorted by path so output is deterministic.
    """
    validator = validator_for(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    return [_format(e) for e in errors]


def validate_file(instance_path, schema_path) -> list[str]:
    schema = load_schema(str(pathlib.Path(schema_path).resolve()))
    instance = json.loads(pathlib.Path(instance_path).read_text(encoding="utf-8"))
    return validate(instance, schema)


def _format(error: jsonschema.ValidationError) -> str:
    location = "$" + "".join(
        f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path
    )
    return f"{location}: {error.message}"


__all__ = [
    "FrontmatterError",
    "SchemaError",
    "load_yaml",
    "load_yaml_text",
    "load_frontmatter",
    "load_schema",
    "validate",
    "validate_file",
    "validator_for",
]
