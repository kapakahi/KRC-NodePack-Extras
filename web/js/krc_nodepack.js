import { app } from "../../scripts/app.js";
import { api as comfyApi } from "../../scripts/api.js";

// The one door to KRC NodePack's public API (krc_public_api.js). NodePack's folder name
// depends on how it was installed (a git clone can use any name; the Comfy Registry
// installs it as krc-nodepack), so the API is found in ComfyUI's own extension list (GET /extensions)
// and imported by that exact URL, the one ComfyUI loaded it from: one module instance
// (sync bus, menus and palettes shared). A node entry loads its modules through
// loadWithNodePack(): it checks the API is there and compatible, and otherwise reports
// why the node is disabled instead of failing with a module error. Mirrors REQUIRED_API
// in utils/krc.py: same major, at least this minor.
const API_FILE = "/krc_public_api.js";
export const REQUIRED_API = { major: 2, minor: 0 };

let apiCheck = null;
let apiModule = null;

// -> the URL ComfyUI imports NodePack's krc_public_api.js from, or null.
async function nodePackApiUrl() {
  try {
    const response = await comfyApi.fetchApi("/extensions", { cache: "no-store" });
    const list = response.ok ? await response.json() : [];
    const found = (Array.isArray(list) ? list : [])
      .find((url) => typeof url === "string" && url.startsWith("/extensions/") && url.endsWith(API_FILE));
    if (!found) return null;
    return typeof comfyApi.fileURL === "function" ? comfyApi.fileURL(found) : found;
  } catch {
    return null;
  }
}

function reportDisabled(label, reason) {
  console.error(`[KRC NodePack Extras] ${label} disabled: ${reason}`);
  try {
    app.extensionManager?.toast?.add({ severity: "error", summary: label, detail: reason, life: 10000 });
  } catch {
    // Older frontends have no toast; the console line is enough.
  }
}

// null when the API is usable, else the reason it isn't (checked once per page).
const MISSING = "KRC NodePack is not installed or didn't load. Install it to use KRC NodePack Extras.";

function checkApi() {
  apiCheck ||= nodePackApiUrl().then((url) => (url ? import(url) : Promise.reject(new Error("not found")))).then(
    (api) => {
      apiModule = api;
      const version = api.KRC_API_VERSION || {};
      if (version.major === REQUIRED_API.major && version.minor >= REQUIRED_API.minor) return null;
      return `needs KRC NodePack public API ${REQUIRED_API.major}.x (>= ${REQUIRED_API.major}.${REQUIRED_API.minor}), `
        + `found ${version.major}.${version.minor}. Update the pack that is older.`;
    },
    () => MISSING,
  );
  return apiCheck;
}

// NodePack's public API module once it checks out, else null (krc.js re-exports it).
export async function nodePackApi() {
  return (await checkApi()) ? null : apiModule;
}

// Run `load` (the node's dynamic imports) once NodePack's API checks out; resolves to its
// result, or null when the node is disabled.
export async function loadWithNodePack(label, load) {
  const reason = await checkApi();
  if (reason) {
    reportDisabled(label, reason);
    return null;
  }
  return load();
}
