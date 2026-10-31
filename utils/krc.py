"""The one door to KRC NodePack for every KRC NodePack Extras node: everything Extras
uses from NodePack comes through its public API (krc_public_api.py), found here.

Call :func:`api` lazily (at route or run time, never at import): ComfyUI imports packs
alphabetically, so this keeps working whatever the folder names are. NodePack is found
through its package attribute ``KRC_PUBLIC_API``, not its folder name.
"""

import json
import os
import sys

# The pack's manifest (krc_pack.json at the pack root): KRC NodePack reads it to know
# Extras is installed, and it is the one place the API requirement is written.
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "krc_pack.json")
with open(MANIFEST_PATH, encoding="utf-8") as _handle:
    MANIFEST = json.load(_handle)

# The public API version Extras is written against: same major, at least this minor.
# Mirrors REQUIRED_API in web/js/krc_nodepack.js (the dev repo's api-check compares them).
REQUIRED_API = tuple(MANIFEST["requires_api"])[:2]

_api = None


def _find_public_api():
    for module in list(sys.modules.values()):
        try:
            candidate = vars(module).get("KRC_PUBLIC_API")
        except TypeError:
            continue
        if candidate is not None and hasattr(candidate, "KRC_API_VERSION"):
            return candidate
    return None


def api():
    """KRC NodePack's public API module; raises a clear error when NodePack is missing or
    its API version doesn't match."""
    global _api
    if _api is not None:
        return _api
    found = _find_public_api()
    if found is None:
        raise RuntimeError(
            "[KRC NodePack Extras] KRC NodePack is not installed or failed to load; "
            "KRC NodePack Extras needs it."
        )
    major, minor = tuple(found.KRC_API_VERSION)[:2]
    if major != REQUIRED_API[0] or minor < REQUIRED_API[1]:
        raise RuntimeError(
            f"[KRC NodePack Extras] needs KRC NodePack public API {REQUIRED_API[0]}.x "
            f"(>= {REQUIRED_API[0]}.{REQUIRED_API[1]}), found {major}.{minor}; update the "
            "pack that is older."
        )
    _api = found
    return _api
