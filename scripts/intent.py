"""Canonical per-screen intent fingerprints; no external dependencies.

This module does NOT read Figma. Live node checks are required before patches.
"""
import hashlib
import json
import os


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj):
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_token(root, ref):
    obj = root
    for part in ref.split("."):
        if not isinstance(obj, dict) or part not in obj:
            raise ValueError(f"Missing design token: {ref}")
        obj = obj[part]
    return obj


def resolve_asset(root, ref):
    """Understands assets.py manifest: images:name, icons:name:variant.

    Legacy/simplified `assets` maps are also supported for experiments.
    Missing asset fingerprints are deterministic placeholders, not hidden errors.
    """
    parts = ref.split(":")
    if len(parts) == 1:
        entry = root.get("assets", {}).get(ref)
    elif parts[0] == "images" and len(parts) == 2:
        entry = root.get("images", {}).get(parts[1])
    elif parts[0] == "icons" and len(parts) in (2, 3):
        item = root.get("icons", {}).get(parts[1])
        if item is None:
            entry = None
        elif len(parts) == 3:
            entry = {"variant": parts[2], "path": item.get("variants", {}).get(parts[2])}
        else:
            entry = item
    else:
        raise ValueError(f"Bad asset reference: {ref}")
    return entry if entry is not None else {"missing": ref}


def asset_source_hashes(entry, assets_path):
    """Hash only the referenced image bytes, not every asset in the manifest."""
    if not isinstance(entry, dict):
        return {}
    paths = []
    if isinstance(entry.get("file"), str):
        paths.append(entry["file"])
    if isinstance(entry.get("path"), str):
        paths.append(entry["path"])
    if isinstance(entry.get("variants"), dict):
        paths.extend(x for x in entry["variants"].values() if isinstance(x, str))
    manifest_dir = os.path.dirname(os.path.abspath(assets_path))
    root = (os.path.dirname(manifest_dir) if os.path.basename(manifest_dir) == "assets"
            else manifest_dir)
    result = {}
    for path in paths:
        real = path if os.path.isabs(path) else os.path.join(root, path)
        try:
            with open(real, "rb") as f:
                h = hashlib.sha256()
                for chunk in iter(lambda: f.read(64 * 1024), b""):
                    h.update(chunk)
                result[path] = h.hexdigest()
        except FileNotFoundError:
            result[path] = "missing"
    return result


def compute_intent(recipe_path, tokens_path, assets_path):
    recipe = read_json(recipe_path)
    tokens = read_json(tokens_path)
    assets = read_json(assets_path)
    if not isinstance(recipe, dict) or not recipe.get("screen_id") or not recipe.get("name"):
        raise ValueError("Recipe must have screen_id and name")
    nodes = recipe.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("Recipe nodes must be an array")
    ids = []
    structure, text, style, asset_map = [], {}, {}, {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("Each recipe node must be an object")
        sid = node.get("semantic_id")
        kind = node.get("type")
        if not isinstance(sid, str) or not sid or not isinstance(kind, str) or not kind:
            raise ValueError("Node requires semantic_id and type")
        if sid in ids:
            raise ValueError(f"Duplicate semantic ID: {sid}")
        parent = node.get("parent", "root")
        if parent != "root" and parent not in ids:
            raise ValueError(f"Parent must precede child: {sid}: {parent}")
        ids.append(sid)
        structure.append({"semantic_id": sid, "type": kind, "parent": parent,
                          "name": node.get("name"), "component": node.get("component"),
                          "layout": node.get("layout", {}), "geometry": node.get("geometry", {}),
                          "properties": node.get("properties", {})})
        if "text" in node:
            if kind != "TEXT" or not isinstance(node["text"], str):
                raise ValueError(f"Only TEXT nodes accept a string text property: {sid}")
            text[sid] = node["text"]
        refs = node.get("tokens", [])
        arefs = node.get("assets", [])
        if not isinstance(refs, list) or not isinstance(arefs, list):
            raise ValueError("tokens and assets must be arrays")
        style[sid] = {"inline": node.get("style", {}),
                      "tokens": {ref: resolve_token(tokens, ref) for ref in refs}}
        for aref in arefs:
            meta = resolve_asset(assets, aref)
            asset_map[aref] = {"metadata": meta, "file_hashes": asset_source_hashes(meta, assets_path)}
    snapshot = {"structure": structure, "text": text, "style": style, "assets": asset_map}
    return {"screen_id": recipe["screen_id"], "name": recipe["name"],
            "hashes": {k: digest(v) for k, v in snapshot.items()},
            "snapshot": snapshot}


def classify(current, target):
    if not current:
        return {"action": "legacy_reconcile", "changed_text": []}
    old, new = current["hashes"], target["hashes"]
    if old["structure"] != new["structure"] or old["assets"] != new["assets"]:
        return {"action": "rebuild", "changed_text": []}
    text_changed = sorted(
        k for k in set(current["snapshot"]["text"]) | set(target["snapshot"]["text"])
        if current["snapshot"]["text"].get(k) != target["snapshot"]["text"].get(k)
    )
    if old["text"] != new["text"] and not text_changed:
        return {"action": "rebuild", "changed_text": []}
    style_changed = old["style"] != new["style"]
    if style_changed and text_changed:
        action = "mixed_patch"
    elif style_changed:
        action = "style_patch"
    elif text_changed:
        action = "text_patch"
    else:
        action = "skip"
    return {"action": action, "changed_text": text_changed}
