from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import Settings
from app.core.views import templates
from app.services.metrics import metrics_for_store, store_from_token

router = APIRouter(tags=["metrics"])
HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


def resolve(session, token):
    settings = Settings()
    store = store_from_token(session, token, settings)
    if store is None:
        raise HTTPException(404, "Link de métricas indisponível.")
    return metrics_for_store(session, store, settings)


@router.get("/metrics/{token}", response_class=HTMLResponse)
def dashboard(request: Request, token: str, session: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="metrics.html",
        context={"metrics": resolve(session, token)},
        headers=HEADERS,
    )


@router.get("/metrics/{token}/data")
def dashboard_data(token: str, session: Session = Depends(get_db)):
    return resolve(session, token)
