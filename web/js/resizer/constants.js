export const NODE_CLASS = "KRC Resizer";
export const API_PREFIX = "/krc_resizer";
export const PREVIEW_SIZE = 350;  // square preview foundation
export const CONTROL_W = 270;
export const FIXED_DOM_W = PREVIEW_SIZE + CONTROL_W + 10;
export const FIXED_DOM_H = 430;
export const NODE_FRAME_W = 21;
export const NODE_FRAME_H = 93;  // Node 1.0 needs extra socket chrome for mask/audio I/O
export const FIXED_NODE_W = FIXED_DOM_W + NODE_FRAME_W - 2;
export const FIXED_NODE_H = FIXED_DOM_H + NODE_FRAME_H - 2;
export const MARGIN = 22;    // canvas margin around source frame (px)
export const GRID = 16;      // quantisation grid (source px)
export const MIN_SOURCE_OVERLAP = 1;   // minimum source/crop intersection (source px)
export const DEFAULT_FPS = 24;


// Default footprints for the two ComfyUI renderers; all resizing uses these bounds.
export const NODE2_CHROME_W = 24;
export const NODE2_CHROME_H = 132;
export const MAX_SIZE_FACTOR = 3;
