import { loadWithNodePack } from "./krc_nodepack.js";

// resizer/panel.js registers the extension; load it once KRC NodePack's API checks out.
await loadWithNodePack("KRC Resizer", () => import("./resizer/panel.js"));
