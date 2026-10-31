import { makeNodeApi, openNumericPopover, stopCanvasEvents } from "../krc.js";

// The REFMODS header meter, as the Loadout Kit's header extension
// (registerLoadout({ header: { right: tokenMeter } })): live token total for the stack
// (their token_count x copies) against the node's budget (their max_total_tokens;
// 0 = none). Per-file counts come from /krc/refmod-loadout/tokens (header-only reads)
// and are cached per id in ctx.state, so edits to X / components / V / A recompute
// instantly. The kit re-renders the meter after every stack or field change.

const { getSharedJson } = makeNodeApi("/krc/refmod-loadout");

// Their max_total_tokens upper bound; mirrors TOKEN_BUDGET_MAX in the node.
const TOKEN_BUDGET_MAX = 1048576;
// Budget popover: the slider covers the common range, typing reaches their max.
const BUDGET_SLIDER_MAX = 32768;
const BUDGET_STEP = 256;

function clampBudget(value) {
  const number = Math.round(Number(value));
  return Number.isFinite(number) ? Math.max(0, Math.min(TOKEN_BUDGET_MAX, number)) : 0;
}

function formatCount(value) {
  return Number(value || 0).toLocaleString();
}

function tokenBudget(ctx) {
  return clampBudget(ctx.getWidget("token_budget"));
}

// Tokens one slot loads, as their loader counts them: each member (one for a standalone
// file, several for a bundle) is skipped when the components pick excludes its modality
// or its V / A strength is 0; the rest are multiplied by copies. S = 0 skips the slot.
function slotTokens(entry, members) {
  if (entry.strength <= 0) {
    return 0;
  }
  const perCopy = members.reduce((sum, member) => {
    const audio = member.kind === "audio";
    const weight = audio ? entry.audio_strength : entry.visual_strength;
    const excluded = entry.components === (audio ? "Visual" : "Audio");
    return weight <= 0 || excluded ? sum : sum + (Number(member.tokens) || 0);
  }, 0);
  return perCopy * entry.copies;
}

// Fetch counts for stack ids we have not seen yet; re-render the meter when they land.
function ensureTokenCounts(ctx, entries) {
  const state = ctx.state;
  state.tokenInfo ||= new Map();
  state.tokenPending ||= new Set();
  const ids = [...new Set(entries.map((entry) => entry.id))]
    .filter((id) => id && !state.tokenInfo.has(id) && !state.tokenPending.has(id));
  if (!ids.length) {
    return;
  }
  ids.forEach((id) => state.tokenPending.add(id));
  const query = ids.map((id) => `id=${encodeURIComponent(id)}`).join("&");
  getSharedJson(`/tokens?${query}`)
    .then(({ ok, data }) => {
      const items = ok && data?.items ? data.items : {};
      ids.forEach((id) => state.tokenInfo.set(id, items[id] || { error: "unreadable" }));
    })
    .catch(() => {
      ids.forEach((id) => state.tokenInfo.set(id, { error: "unreadable" }));
    })
    .finally(() => {
      ids.forEach((id) => state.tokenPending.delete(id));
      if (!ctx.isDestroyed()) ctx.refresh();
    });
}

function tokenUsage(ctx, entries) {
  const rows = [];
  let used = 0;
  let pending = false;
  entries.forEach((entry) => {
    const row = { slot: entry.slot + 1, name: ctx.card(entry.id).title, copies: entry.copies };
    const info = ctx.state.tokenInfo?.get(entry.id);
    if (!entry.enabled || entry.strength <= 0) {
      row.state = "off";
    } else if (!info) {
      row.state = "pending";
      pending = true;
    } else if (info.error || !Array.isArray(info.members)) {
      row.state = "unknown";
    } else {
      row.state = "ok";
      row.tokens = slotTokens(entry, info.members);
      row.perCopy = entry.copies ? row.tokens / entry.copies : 0;
      used += row.tokens;
    }
    rows.push(row);
  });
  return { used, rows, pending };
}

function meterTitle(usage, budget) {
  const lines = ["Tokens after copies"];
  usage.rows.forEach((row) => {
    let detail = "?";
    if (row.state === "off") detail = "off";
    else if (row.state === "pending") detail = "…";
    else if (row.state === "ok") {
      detail = row.copies > 1
        ? `${formatCount(row.perCopy)} × ${row.copies} = ${formatCount(row.tokens)}`
        : formatCount(row.tokens);
    }
    lines.push(`${row.slot}. ${row.name}: ${detail}`);
  });
  if (!usage.rows.length) lines.push("(empty stack)");
  lines.push("");
  lines.push(budget > 0
    ? `Budget ${formatCount(budget)}; over budget fails the run. Click to change.`
    : "No budget. Click to set one.");
  return lines.join("\n");
}

function openBudgetEditor(ctx, anchor) {
  // One popover at a time: joins the kit's strip editors.
  ctx.closeEditor();
  const editor = openNumericPopover({
    root: ctx.root,
    anchor,
    initialValue: tokenBudget(ctx),
    classes: {
      popover: "krc-strength-popover",
      input: "krc-strength-value-input",
      slider: "krc-strength-slider",
      nudge: "krc-strength-nudge",
      sliderRow: "krc-strength-slider-row",
    },
    ariaLabel: "Edit token budget",
    inputMode: "numeric",
    inputAriaLabel: "Token budget (0 = none)",
    slider: {
      min: 0,
      max: BUDGET_SLIDER_MAX,
      step: BUDGET_STEP,
      value: (value) => Math.min(BUDGET_SLIDER_MAX, clampBudget(value)),
      ariaLabel: "Token budget slider",
    },
    nudge: {
      step: BUDGET_STEP,
      downTitle: `Decrease by ${BUDGET_STEP}`,
      downAriaLabel: `Decrease token budget by ${BUDGET_STEP}`,
      upTitle: `Increase by ${BUDGET_STEP}`,
      upAriaLabel: `Increase token budget by ${BUDGET_STEP}`,
    },
    themeId: ctx.themeId(),
    formatValue: (value) => String(clampBudget(value)),
    sanitizeInput: (value) => String(value ?? "").replace(/\D/g, ""),
    isPartialInput: (value) => !value,
    normalizeValue: clampBudget,
    onCommit: (draftValue) => {
      const next = clampBudget(draftValue);
      if (next !== tokenBudget(ctx)) {
        ctx.setWidget("token_budget", next);
      }
      ctx.refresh();
    },
    // Opening another editor closes this one first, so untracking here is safe.
    onClose: () => ctx.trackEditor(null),
  });
  ctx.trackEditor(editor);
}

export function tokenMeter(ctx) {
  const entries = ctx.entries();
  ensureTokenCounts(ctx, entries);
  const budget = tokenBudget(ctx);
  const usage = tokenUsage(ctx, entries);
  const over = budget > 0 && usage.used > budget;

  const meter = document.createElement("button");
  meter.type = "button";
  meter.className = "krc-rm-token-meter";
  meter.classList.toggle("is-over", over);
  meter.classList.toggle("has-budget", budget > 0);
  meter.title = meterTitle(usage, budget);
  meter.setAttribute("aria-label", "Token budget");
  stopCanvasEvents(meter);
  meter.addEventListener("click", (event) => {
    event.stopPropagation();
    openBudgetEditor(ctx, meter);
  });

  // The kit's field-label look ("T:", like the strip's "S:").
  const label = document.createElement("span");
  label.className = "krc-kit-field-label";
  label.textContent = "T:";
  // The track is always there; with no budget there's nothing to fill against, so it
  // stays empty (and still says "click to set one" by being there).
  const bar = document.createElement("span");
  bar.className = "krc-rm-token-bar";
  const fill = document.createElement("span");
  fill.className = "krc-rm-token-fill";
  fill.style.width = `${budget > 0 ? Math.min(100, (usage.used / budget) * 100) : 0}%`;
  bar.append(fill);

  // used / budget in their own colours: usage = the fill's colour, budget = gold
  // ("off" when there's no budget); over budget turns usage red.
  const value = document.createElement("span");
  value.className = "krc-rm-token-value";
  const used = document.createElement("span");
  used.className = "krc-rm-token-used";
  used.textContent = usage.pending && !usage.used ? "…" : formatCount(usage.used);
  const separator = document.createElement("span");
  separator.className = "krc-rm-token-sep";
  separator.textContent = " / ";
  const limit = document.createElement("span");
  limit.className = "krc-rm-token-budget";
  limit.classList.toggle("is-off", budget <= 0);
  limit.textContent = budget > 0 ? formatCount(budget) : "off";
  value.append(used, separator, limit);

  meter.append(label, bar, value);
  return meter;
}
