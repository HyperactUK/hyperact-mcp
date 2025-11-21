from __future__ import annotations

import os

from starlette.responses import JSONResponse

from src.lib import mcp
import src.resources 
import src.tools


@mcp.custom_route("/", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": mcp.name})


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT")

    if not transport:
        transport = "http" if os.getenv("PORT") else "stdio"

    run_kwargs: dict[str, object] = {}
    if transport in {"http", "sse", "streamable-http"}:
        run_kwargs["host"] = os.getenv("HOST", "0.0.0.0")
        run_kwargs["port"] = int(os.getenv("PORT", "8080"))

    mcp.run(transport=transport, **run_kwargs)
