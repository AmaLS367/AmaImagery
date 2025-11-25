from __future__ import annotations
import argparse
import importlib
import json
import sys
from typing import Any, Iterable, Tuple, Dict, List

# Make project root importable regardless of CWD
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

def _is_fastapi_instance(obj) -> bool:
    return hasattr(obj, "routes") and hasattr(obj, "openapi") and hasattr(obj, "add_api_route")

def _load_app(target: str):
    """
    target format:
      module:attr
    attr может быть экземпляром FastAPI или фабрикой, возвращающей его.
    """
    if ":" not in target:
        raise ValueError("Expected --app format 'module:attr'")
    mod_name, attr = target.split(":", 1)
    mod = importlib.import_module(mod_name)
    obj = getattr(mod, attr)

    # Если это уже FastAPI-приложение (экземпляр), вернуть как есть.
    if _is_fastapi_instance(obj):
        return obj

    # Иначе, если это фабрика — вызвать и проверить результат.
    if callable(obj):
        app = obj()
        if _is_fastapi_instance(app):
            return app
        raise TypeError(f"--app '{target}' returned non-FastAPI object: {type(app)!r}")

    raise TypeError(f"--app '{target}' is neither FastAPI instance nor factory, got: {type(obj)!r}")


def _route_id(route) -> Tuple[str, str]:
    # Starlette Route has .methods and .path
    methods = list(route.methods or ["GET"])
    method = methods[0].upper()
    return method, route.path

def _endpoint_origin(route) -> str:
    # try get module name of endpoint for diagnostics
    ep = getattr(route, "endpoint", None)
    mod = getattr(ep, "__module__", "")
    return mod or "<unknown>"

def find_duplicates(app, ignore: Iterable[str]) -> Dict[Tuple[str, str], List[str]]:
    from starlette.routing import Route
    seen: Dict[Tuple[str, str], List[str]] = {}
    for r in app.routes:
        if isinstance(r, Route):
            key = _route_id(r)
            if key[1] in ignore:
                continue
            seen.setdefault(key, []).append(_endpoint_origin(r))
    return {k: v for k, v in seen.items() if len(v) > 1}

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Detect duplicate FastAPI routes")
    p.add_argument("--app", default="app.main:app", help="Module:attr to load FastAPI app")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    p.add_argument("--ignore", nargs="*", default=[], help="Ignore exact paths")
    args = p.parse_args(argv)

    app = _load_app(args.app)
    dups = find_duplicates(app, set(args.ignore))

    if args.json:
        out = {f"{m} {p}": origins for (m, p), origins in sorted(dups.items())}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        if not dups:
            print("No duplicate routes found.")
        else:
            print("Duplicate routes detected:")
            for (m, p), origins in sorted(dups.items()):
                origins_str = ", ".join(origins)
                print(f"{m} {p}  ->  {origins_str}")

    return 1 if dups else 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
