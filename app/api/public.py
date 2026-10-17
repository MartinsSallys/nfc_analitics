from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.views import templates
from app.models import Destination, EventType, Link
from app.services.events import record_event
from app.services.plates import PlateUnavailableError
from app.services.public import active_links, public_context

router = APIRouter(tags=["public"])
LABELS = {"google": "Google", "whatsapp": "WhatsApp", "instagram": "Instagram"}
EVENTS = {
    Destination.GOOGLE: EventType.GOOGLE_CLICK,
    Destination.WHATSAPP: EventType.WHATSAPP_CLICK,
    Destination.INSTAGRAM: EventType.INSTAGRAM_CLICK,
}
HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}


def unavailable(request: Request, status: int = 404):
    return templates.TemplateResponse(
        request=request,
        name="unavailable.html",
        context={},
        status_code=status,
        headers=HEADERS,
    )


@router.get("/p/{plate_code}", response_class=HTMLResponse)
def public(request: Request, plate_code: str, session: Session = Depends(get_db)):
    try:
        plate, store = public_context(session, plate_code)
        links = active_links(session, store.id)
        response = templates.TemplateResponse(
            request=request,
            name="public.html",
            context={"store": store, "plate": plate, "links": links, "labels": LABELS},
            headers=HEADERS,
        )
        record_event(session, plate_code, EventType.PAGE_VIEW)
        session.commit()
        return response
    except PlateUnavailableError:
        session.rollback()
        return unavailable(request)
    except IntegrityError:
        session.rollback()
        return unavailable(request, 503)


@router.get("/r/{plate_code}/{destination}")
def redirect(
    request: Request, plate_code: str, destination: str, session: Session = Depends(get_db)
):
    try:
        kind = Destination(destination)
    except ValueError:
        return unavailable(request)
    try:
        plate, store = public_context(session, plate_code)
        link = session.scalar(
            select(Link)
            .where(Link.store_id == store.id, Link.destination == kind, Link.is_active.is_(True))
            .with_for_update(read=True)
            .execution_options(populate_existing=True)
        )
        if link is None:
            raise PlateUnavailableError()
        url = link.url
        record_event(session, plate.plate_code, EVENTS[kind])
        session.commit()
        return RedirectResponse(url, status_code=302, headers=HEADERS)
    except PlateUnavailableError:
        session.rollback()
        return unavailable(request)
    except IntegrityError:
        session.rollback()
        return unavailable(request, 503)
