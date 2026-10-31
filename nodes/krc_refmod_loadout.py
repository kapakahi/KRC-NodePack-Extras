import logging
import os
import sys

from ..utils.krc import api


logger = logging.getLogger(__name__)

# The Loadout Kit this node is built on (KRC NodePack public API 1.4). The kit owns the
# stack, presets + trigger, card resolving (healed paths), the missing report and usage;
# this node only builds the H3 bundle. Its presets live in KRC NodePack's krc.db (kind
# kit:refmod_loadout); the kit id is also its data folder under krc_nodes/.
KIT_ID = "refmod_loadout"
# Fixed slot count; mirrors MiniMaxH3RefModsLoader.MAX_SLOTS (8 mod_N inputs).
SLOT_COUNT = 8
# MiniMaxH3RefModsLoader's per-slot ranges (strength_N / visual_strength_N /
# audio_strength_N 0..1, copies_N 1..10, components_N one of REFMOD_COMPONENTS).
REFMOD_COMPONENTS = ["All", "Visual", "Audio"]
# Their max_total_tokens upper bound.
TOKEN_BUDGET_MAX = 1048576

# ComfyUI-MiniMaxH3Mod's loader. We build its H3_REF_MODS output by calling it, so the
# bundle format stays theirs.
H3_LOADER_CLASS = "MiniMaxH3RefModsLoader"

_KIT = None


def _kit():
    """Created on first use (INPUT_TYPES), so pack load order never matters."""
    global _KIT
    if _KIT is None:
        krc = api()
        _KIT = krc.loadout_kit(
            KIT_ID,
            source={"kind": "model", "folder": "refmods"},
            slots=SLOT_COUNT,
            # API 1.7: the Portal names the kit by `label`; Prompt Vault shows a
            # "RefMod Preset" row (opt-in per node) because of `prompt_vault`.
            label="RefMod Loadout",
            short_label="RefMod",
            prompt_vault=True,
            fields=[
                krc.kit_field("strength", "float", 0, 1, default=1.0, step=0.01, label="S", title="Strength"),
                krc.kit_field("copies", "int", 1, 10, default=1, label="X", title="Copies"),
                krc.kit_field("components", "enum", options=REFMOD_COMPONENTS, title="Components"),
                krc.kit_field("visual_strength", "float", 0, 1, default=1.0, step=0.01, label="V",
                              title="Visual strength", dim_when={"components": ["Audio"]}),
                krc.kit_field("audio_strength", "float", 0, 1, default=1.0, step=0.01, label="A",
                              title="Audio strength", dim_when={"components": ["Visual"]}),
            ],
        )
    return _KIT


def _h3_loader_class():
    try:
        import nodes as comfy_nodes
    except ImportError:
        return None
    return getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {}).get(H3_LOADER_CLASS)


def _h3_mod_dirs(loader_cls):
    """The folders their loader resolves mod names against (first match wins there)."""
    module = sys.modules.get(getattr(loader_cls, "__module__", ""))
    search_dirs = getattr(module, "_mod_search_dirs", None)
    if callable(search_dirs):
        try:
            return list(search_dirs())
        except Exception:  # noqa: BLE001
            pass
    try:
        import folder_paths
        return list(folder_paths.get_folder_paths("refmods"))
    except Exception:  # noqa: BLE001
        return []


def _h3_mod_name(path, dirs):
    """Absolute .safetensors path -> their relative mod name ("sub/name", no extension)."""
    if not path or not path.endswith(".safetensors"):
        return ""
    target = os.path.realpath(path)
    for folder in dirs:
        root = os.path.realpath(folder)
        try:
            contained = os.path.commonpath((root, target)) == root
        except ValueError:
            contained = False
        if contained:
            return os.path.relpath(target, root)[: -len(".safetensors")].replace("\\", "/")
    return ""


def _coerce_budget(value):
    try:
        budget = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(TOKEN_BUDGET_MAX, budget))


class RefModLoadoutNode:
    DESCRIPTION = (
        "Pick MiniMax H3 RefMods from the Model Library into one 8-slot stack, save it as "
        "presets, and output the H3_REF_MODS bundle for Apply H3 RefMod."
    )
    CATEGORY = "KRC NodePack Extras"
    RETURN_TYPES = ("H3_REF_MODS", "STRING")
    RETURN_NAMES = ("mods", "prompt_hint")
    FUNCTION = "resolve_stack"

    @classmethod
    def INPUT_TYPES(cls):
        return _kit().input_types(required={
            # Their max_total_tokens: 0 = no budget; over budget fails the run.
            "token_budget": ("INT", {"default": 0, "min": 0, "max": TOKEN_BUDGET_MAX}),
        })

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return _kit().is_changed(**kwargs)

    def resolve_stack(self, token_budget=0, **kwargs):
        loadout = _kit().resolve(**kwargs)
        mods, prompt_hint = self._load_h3_mods(loadout.entries, _coerce_budget(token_budget))
        return {"ui": loadout.ui, "result": (mods, prompt_hint)}

    def _load_h3_mods(self, entries, token_budget=0):
        if not entries:
            return [], ""
        loader_cls = _h3_loader_class()
        if loader_cls is None:
            raise RuntimeError(
                "[KRC RefMod Loadout] ComfyUI-MiniMaxH3Mod is not installed or failed to load; "
                "it is required to build the RefMod bundle."
            )
        dirs = _h3_mod_dirs(loader_cls)
        kwargs = {}
        for slot, entry in enumerate(entries, start=1):
            name = _h3_mod_name(entry["path"], dirs)
            if not name:
                raise RuntimeError(
                    f"[KRC RefMod Loadout] {entry['path']} is not inside a RefMod folder "
                    "(models/refmods) that ComfyUI-MiniMaxH3Mod can load from."
                )
            kwargs[f"mod_{slot}"] = name
            kwargs[f"strength_{slot}"] = entry["strength"]
            kwargs[f"copies_{slot}"] = entry["copies"]
            kwargs[f"components_{slot}"] = entry["components"]
            kwargs[f"visual_strength_{slot}"] = entry["visual_strength"]
            kwargs[f"audio_strength_{slot}"] = entry["audio_strength"]
        mods, prompt_hint = loader_cls().load(show_info=False, max_total_tokens=token_budget, **kwargs)
        return mods, prompt_hint


# Register the token-count route (the meter's). Presets are the kit's routes. Guarded.
from ..utils.refmod_loadout.routes import register_routes
register_routes()


NODE_CLASS_MAPPINGS = {"KRC RefMod Loadout": RefModLoadoutNode}
NODE_DISPLAY_NAME_MAPPINGS = {"KRC RefMod Loadout": "KRC RefMod Loadout"}
