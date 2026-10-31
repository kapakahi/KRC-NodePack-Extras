// The one door to KRC NodePack for every KRC NodePack Extras node module: the names Extras
// uses from NodePack's public API (krc_public_api.js), re-exported. The module itself
// comes from krc_nodepack.js, which finds it by the URL ComfyUI loaded it from (any
// NodePack folder name; one module instance, so the sync bus, menus and palettes are
// shared). Node entries load their modules through loadWithNodePack(), which checks the
// API first, so by the time this runs it's there. A new name Extras imports from here
// goes in this list (the dev repo's check compares the two).
import { nodePackApi } from "./krc_nodepack.js";

const api = (await nodePackApi()) || {};

export const {
  KRC_API_VERSION,
  applyNodeCanvasColors,
  applyNodePalette,
  buildNodePaletteField,
  bindNodeShellSizeClamp,
  debounce,
  domSummary,
  ensureSharedStylesheets,
  ensureStylesheet,
  imageStatsFromElements,
  installCanvasDragSelectionGuard,
  installKrcStatsAggregator,
  makeNodeApi,
  modalPaletteIdForNode,
  openKrcModal,
  openNumericPopover,
  registerLoadout,
  roughJsonBytes,
  stopCanvasEvents,
} = api;
