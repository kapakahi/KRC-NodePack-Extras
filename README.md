# KRC NodePack Extras

Optional nodes built on [KRC NodePack](https://github.com/PLACEHOLDER/KRC-NodePack).

KRC NodePack never depends on another custom-node pack. Nodes that do, or that are
standalone utilities outside the KRC ecosystem, live here instead.

## Requirements

- **KRC NodePack** (any install folder name). KRC NodePack Extras uses NodePack's library, cards, presets and
  styling through its public API. Without it, or with an incompatible version, the
  nodes report a clear error.
- Per node, see below.

## Nodes

### KRC RefMod Loadout

A card-based loader for MiniMax H3 RefMods: one stack of 8 slots filled from the KRC
Model Library (Portal), with per-slot strength, copies, components and visual / audio
strength, a live token meter with an optional budget, and presets with triggers.

- **Needs:** [ComfyUI-MiniMaxH3Mod](https://github.com/Luisacaotica/ComfyUI-MiniMaxH3Mod)
  to run; RefMod files go in `models/refmods`.
- **Outputs:** `mods` (`H3_REF_MODS`) and `prompt_hint`, the same as their RefMods
  Loader, so it feeds Apply H3 RefMod and H3 RefMod Text Encode.
- Presets are stored with KRC NodePack's data (`krc_nodes/refmod_loadout/`).

### KRC Resizer

An image resizer / outpainter with a live preview: crop, pad, transform and mask
controls, aspect and output sizing, frame handling for image batches, passthrough and DISABLE.

- **Needs:** nothing beyond KRC NodePack (it uses NodePack's palettes and popovers).

### KRC Frame Router

Routes frames by count: one frame goes out `image`, a batch of two or more goes out
`video`, and the other output sends nothing. Made for MiniMax H3 **Reference to Video**:
wire `image` into its reference image input and `video` into its reference video input,
and a still or a clip from the same Resizer reaches the right one. With nothing coming in
(a disabled or muted node before it), both outputs send nothing.

- **Needs:** nothing (a standalone V3 node).

## Install

Clone into `ComfyUI/custom_nodes/` next to KRC NodePack (`KRC-NodePack`) and restart ComfyUI.
