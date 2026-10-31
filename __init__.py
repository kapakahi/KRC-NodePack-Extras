"""
KRC NodePack Extras
===================
Optional KRC nodes that live outside KRC NodePack: nodes that depend on another
custom-node pack (incubating until ComfyUI supports the technique natively, e.g. RefMod
Loadout) and standalone utilities (e.g. Resizer, Frame Router).

Requires KRC NodePack. Everything used from it goes through its public API
(``krc_public_api``), found lazily at run time (never at import, so load order and
folder names don't matter). All nodes register under the ``KRC NodePack Extras``
category.
"""

# Version and API requirement live in krc_pack.json (KRC NodePack reads it too).
from .utils.krc import MANIFEST as _MANIFEST

__version__ = _MANIFEST["version"]

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# RefMod Loadout (MiniMax H3 RefMods; needs ComfyUI-MiniMaxH3Mod to run). Guarded so one
# node can never take down the rest of the pack.
try:
    from .nodes.krc_refmod_loadout import NODE_CLASS_MAPPINGS as _rm_c, NODE_DISPLAY_NAME_MAPPINGS as _rm_d
    NODE_CLASS_MAPPINGS.update(_rm_c)
    NODE_DISPLAY_NAME_MAPPINGS.update(_rm_d)
except Exception as _rm_err:
    print(f"[KRC NodePack Extras] Warning: RefMod Loadout failed to load: {_rm_err}")

# Resizer (image resizer / outpainter; standalone, only borrows KRC styling).
try:
    from .nodes.krc_resizer import NODE_CLASS_MAPPINGS as _rz_c, NODE_DISPLAY_NAME_MAPPINGS as _rz_d
    NODE_CLASS_MAPPINGS.update(_rz_c)
    NODE_DISPLAY_NAME_MAPPINGS.update(_rz_d)
except Exception as _rz_err:
    print(f"[KRC NodePack Extras] Warning: Resizer failed to load: {_rz_err}")

# Frame Router (one frame -> image, a batch -> video; standalone, a V3 node).
try:
    from .nodes.krc_frame_router import NODE_CLASS_MAPPINGS as _fr_c, NODE_DISPLAY_NAME_MAPPINGS as _fr_d
    NODE_CLASS_MAPPINGS.update(_fr_c)
    NODE_DISPLAY_NAME_MAPPINGS.update(_fr_d)
except Exception as _fr_err:
    print(f"[KRC NodePack Extras] Warning: Frame Router failed to load: {_fr_err}")

WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY", "__version__"]

print(f"[KRC NodePack Extras] v{__version__} - {len(NODE_CLASS_MAPPINGS)} nodes registered (requires KRC NodePack)")
