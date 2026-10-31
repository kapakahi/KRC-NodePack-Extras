"""Token counts for RefMod files, read from the safetensors header only (no tensors).

Mirrors ComfyUI-MiniMaxH3Mod's ``H3RefMod.token_count``: audio = 2 * T; image/video =
T * (latent_h // 2) * (latent_w // 2), with T = 1 for images. A v5 bundle reports one
entry per member (tensor ``ref_<i>``) so the node can apply the components pick and the
per-modality strengths itself; a standalone file reports its single ``latent``.
"""

import json
import os
import struct
import threading

# Header keys their pack embeds the RefMod metadata under (current, legacy audio).
META_KEYS = ("refmod_meta", "audio_refmod_meta")
MAX_HEADER_BYTES = 64 * 1024 * 1024

_CACHE = {}  # path -> ((mtime_ns, size), members)
_LOCK = threading.Lock()


def _read_header(path):
    with open(path, "rb") as handle:
        raw = handle.read(8)
        if len(raw) != 8:
            raise ValueError("not a safetensors file")
        (length,) = struct.unpack("<Q", raw)
        if not 0 < length <= MAX_HEADER_BYTES:
            raise ValueError("bad safetensors header length")
        header = json.loads(handle.read(length))
    if not isinstance(header, dict):
        raise ValueError("bad safetensors header")
    return header


def _read_meta(header, path):
    metadata = header.get("__metadata__") or {}
    for key in META_KEYS:
        if key in metadata:
            return json.loads(metadata[key])
    # Legacy sidecar ({name}.json), as their read_refmod_meta falls back to.
    sidecar = path[: -len(".safetensors")] + ".json"
    if os.path.isfile(sidecar):
        with open(sidecar, encoding="utf-8") as handle:
            return json.load(handle)
    return None


def _member(meta, shape):
    kind = meta.get("kind", "image")
    if kind == "audio":
        return {"kind": "audio", "tokens": 2 * int(shape[-1])}
    video = len(shape) == 5
    latent_h = int(meta.get("latent_h", shape[3] if video else 0))
    latent_w = int(meta.get("latent_w", shape[4] if video else 0))
    latent_t = 1 if kind == "image" else int(meta.get("latent_t", shape[2] if video else shape[-1]))
    return {"kind": kind, "tokens": latent_t * (latent_h // 2) * (latent_w // 2)}


def _tensor_shape(header, name):
    tensor = header.get(name)
    shape = tensor.get("shape") if isinstance(tensor, dict) else None
    if not isinstance(shape, list) or not shape:
        raise ValueError(f"missing tensor {name}")
    return shape


def refmod_members(path):
    """[{kind, tokens}, ...] for one RefMod file; raises on an unreadable file."""
    stat = os.stat(path)
    signature = (stat.st_mtime_ns, stat.st_size)
    with _LOCK:
        cached = _CACHE.get(path)
    if cached and cached[0] == signature:
        return cached[1]
    header = _read_header(path)
    meta = _read_meta(header, path)
    if not isinstance(meta, dict):
        raise ValueError("no RefMod metadata")
    if meta.get("kind") == "bundle":
        refs = meta.get("members")
        if not isinstance(refs, list) or not refs:
            raise ValueError("bundle has no members")
        members = [_member(ref, _tensor_shape(header, f"ref_{i}")) for i, ref in enumerate(refs)]
    else:
        members = [_member(meta, _tensor_shape(header, "latent"))]
    with _LOCK:
        _CACHE[path] = (signature, members)
    return members


def token_counts(resolved):
    """{id: {"members": [...]}} or {id: {"error": "missing" | "unreadable"}} for each id
    of KRC NodePack's resolve_models() result ({id: {"path"} | {"error"}})."""
    out = {}
    for library_id, record in resolved.items():
        path = record.get("path") or ""
        if record.get("error") or not path:
            out[library_id] = {"error": "missing"}
            continue
        try:
            out[library_id] = {"members": refmod_members(path)}
        except (OSError, ValueError, TypeError, KeyError, struct.error):
            out[library_id] = {"error": "unreadable"}
    return out
