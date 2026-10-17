import logging
from urllib.parse import urlsplit

from fastapi import Request
from starlette.responses import JSONResponse

# URLs privadas contêm segredos: não registrar caminhos reais nas access logs.
logging.getLogger("uvicorn.access").disabled = True
logger = logging.getLogger("nfc.requests")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)


async def security_headers(request: Request, call_next):
    settings = request.app.state.settings
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        expected = (
            str(settings.public_base_url).rstrip("/")
            if settings.environment == "production"
            else str(request.base_url).rstrip("/")
        )
        if origin and origin.rstrip("/") != expected:
            return JSONResponse({"detail": "Origem não permitida."}, status_code=403)
    if settings.environment == "production":
        if request.url.hostname != urlsplit(str(settings.public_base_url)).hostname:
            return JSONResponse({"detail": "Host não permitido."}, status_code=400)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    )
    if settings.environment != "production" and request.url.path in {"/docs", "/redoc"}:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "base-uri 'none'; frame-ancestors 'none'"
        )
    if request.url.path.startswith(("/metrics/", "/admin", "/stores")):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    route = request.scope.get("route")
    # route.path é o padrão (/metrics/{token}), nunca o token recebido.
    logger.info(
        "%s %s %d", request.method, getattr(route, "path", "unmatched"), response.status_code
    )
    return response
