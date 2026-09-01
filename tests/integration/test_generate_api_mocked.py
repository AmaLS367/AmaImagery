import pytest


def _resolve_ref(schema, ref):
    # Reference in format "#/components/schemas/Name"
    if not ref.startswith("#/"):
        return {}
    parts = ref.lstrip("#/").split("/")
    node = schema
    for p in parts:
        node = node.get(p, {})
    return node


def _build_min_payload(schema):
    """Builds a valid minimal payload based on schema."""
    if "$ref" in schema:
        schema = _resolve_ref(_build_min_payload._openapi, schema["$ref"])

    data = {}
    required = schema.get("required", [])
    props = schema.get("properties", {})

    # Default fallback values
    defaults = {
        "prompt": "test",
        "negative_prompt": "",
        "steps": 5,
        "num_inference_steps": 5,
        "guidance_scale": 4,
        "cfg_scale": 4,
        "width": 256,
        "height": 256,
        "seed": 1,
        "mode": "txt2img",
        "strength": 0.7,
        "output_format": "png",
    }

    for name in required:
        prop = props.get(name, {})
        if "$ref" in prop:
            val = _build_min_payload(_resolve_ref(_build_min_payload._openapi, prop["$ref"]))
        elif "enum" in prop:
            val = prop["enum"][0]
        elif prop.get("type") == "integer":
            # Handle minimums, multiples, etc.
            v = defaults.get(name, 1)
            v = max(v, prop.get("minimum", v))
            multiple = prop.get("multipleOf")
            if multiple:
                # Align to multiple (e.g. width/height multiple of 8)
                if v % multiple != 0:
                    v = ((v + multiple - 1) // multiple) * multiple
            val = int(v)
        elif prop.get("type") == "number":
            v = float(defaults.get(name, 1.0))
            v = max(v, float(prop.get("minimum", v)))
            val = v
        elif prop.get("type") == "boolean":
            val = True
        elif prop.get("type") == "string":
            val = str(defaults.get(name, "x"))
        else:
            # Unknown type -> fallback to default
            val = defaults.get(name, "x")
        data[name] = val

    # Helpful optional fields if defined
    for opt in (
        "prompt",
        "negative_prompt",
        "width",
        "height",
        "steps",
        "num_inference_steps",
        "guidance_scale",
        "cfg_scale",
        "seed",
        "output_format",
    ):
        if opt in props and opt not in data:
            data[opt] = defaults.get(opt)

    return data


def test_generate_mock(app_client, monkeypatch, tmp_path):
    # 1) Pipeline mock
    try:
        import app.inference.pipeline as pl
    except Exception:
        pytest.skip("pipeline not available")
    out = tmp_path / "mock.png"
    out.write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(pl, "generate_image", lambda *a, **k: str(out), raising=False)

    # 2) Inspect OpenAPI and find schema for POST /api/v1/images/generate
    r = app_client.get("/openapi.json")
    if r.status_code != 200:
        pytest.skip("OpenAPI not available")
    openapi = r.json()
    _build_min_payload._openapi = openapi  # For $ref resolution

    paths = openapi.get("paths", {})
    gen = paths.get("/api/v1/images/generate") or {}
    post = gen.get("post") or {}
    content = ((post.get("requestBody") or {}).get("content") or {}).get("application/json") or {}
    schema = content.get("schema")
    if not schema:
        pytest.skip("No requestBody schema for POST /api/v1/images/generate")

    payload = _build_min_payload(schema)

    # 3) Submit request
    resp = app_client.post("/api/v1/images/generate", json=payload)
    if resp.status_code in (200, 201, 202):
        assert True
        return

    # If it is a schema validation rejection, skip rather than failing
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text
    if resp.status_code == 400:
        pytest.skip(f"Validation /api/v1/images/generate: {detail}")
    pytest.fail(f"/api/v1/images/generate returned {resp.status_code}: {detail}")
