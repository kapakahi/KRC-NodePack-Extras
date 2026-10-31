"""KRC RefMod Loadout API route: per-file token counts for the header meter. The stack,
presets and their routes are KRC NodePack's Loadout Kit (/krc/loadout/refmod_loadout/...);
the RefMod library itself is Model Library's (modelType "refmods")."""

from aiohttp import web

try:
    from server import PromptServer
except ImportError:  # outside ComfyUI (tests)
    PromptServer = None

from ..krc import api
from .tokens import token_counts

_ROUTES_REGISTERED = False

# Counts follow the files on disk; never serve them from a browser/proxy cache.
_NO_STORE = {"Cache-Control": "no-store"}


def register_routes():
    global _ROUTES_REGISTERED
    if PromptServer is None or _ROUTES_REGISTERED:
        return
    _ROUTES_REGISTERED = True

    routes = PromptServer.instance.routes

    # Per-file token counts for the header meter: ?id=..&id=.. -> {"items": {id: ...}}.
    @routes.get("/krc/refmod-loadout/tokens")
    async def get_tokens(request):
        ids = list(dict.fromkeys(item.strip() for item in request.query.getall("id", []) if item.strip()))
        resolved = await api().resolve_models_async(ids)
        return web.json_response({"items": token_counts(resolved)}, headers=_NO_STORE)
