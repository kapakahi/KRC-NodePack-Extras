import { loadWithNodePack } from "./krc_nodepack.js";

// KRC RefMod Loadout is a Loadout Kit node (KRC NodePack public API 1.4): the kit builds
// the preset panel, the 8-slot stack and the S / X / components / V / A strip from the
// Python kit "refmod_loadout"; this adds only the REFMODS header's token meter.
const STYLE_VERSION = "0.2.0";

const loaded = await loadWithNodePack("KRC RefMod Loadout", async () => {
  const [krc, meter] = await Promise.all([
    import("./krc.js"),
    import("./refmod_loadout/token_meter.js"),
  ]);
  return { ...krc, tokenMeter: meter.tokenMeter };
});

if (loaded) {
  const { ensureStylesheet, registerLoadout, tokenMeter } = loaded;
  // The meter's own look; everything else is the kit's.
  ensureStylesheet("krc-refmod-loadout-css", "./krc_refmod_loadout.css", import.meta.url, {
    version: STYLE_VERSION,
    ready: true,
  });
  registerLoadout({
    nodeType: "KRC RefMod Loadout",
    kit: "refmod_loadout",
    noun: "RefMod",
    hiddenWidgets: { token_budget: 0 },
    header: { right: tokenMeter },
  });
}
