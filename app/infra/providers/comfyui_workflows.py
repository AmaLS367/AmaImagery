from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.config import settings


DEFAULT_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / "config" / "comfyui_default_workflow.json"
DEFAULT_MAP_PATH = Path(__file__).resolve().parents[2] / "config" / "comfyui_default_workflow_map.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_workflow_bundle() -> tuple[dict[str, Any], dict[str, Any]]:
    workflow_path = settings.comfyui_workflow_path or DEFAULT_WORKFLOW_PATH
    workflow_map_path = settings.comfyui_workflow_map_path or DEFAULT_MAP_PATH
    return _load_json(workflow_path), _load_json(workflow_map_path)


def _set_nested(target: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: Any = target
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def inject_request(workflow: dict[str, Any], workflow_map: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    rendered = deepcopy(workflow)
    for semantic_key, mapping in workflow_map.get("fields", {}).items():
        if semantic_key not in values or values[semantic_key] is None:
            continue
        node = rendered[str(mapping["node"])]
        _set_nested(node, mapping["path"], values[semantic_key])
    return rendered


def output_node_id(workflow_map: dict[str, Any]) -> str | None:
    node = workflow_map.get("output", {}).get("node")
    return str(node) if node is not None else None
