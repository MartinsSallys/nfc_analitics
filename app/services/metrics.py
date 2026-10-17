import hashlib
import hmac
from datetime import datetime, time, timedelta
from secrets import token_urlsafe
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Event, EventType, Plate, Store


def token_digest(token: str, settings: Settings) -> str:
    return hmac.new(
        settings.secret_key.get_secret_value().encode(), token.encode(), hashlib.sha256
    ).hexdigest()


def rotate_metrics_token(session: Session, store: Store, settings: Settings) -> str:
    token = token_urlsafe(32)
    store.metrics_token_hash = token_digest(token, settings)
    session.commit()
    return token


def store_from_token(session: Session, token: str, settings: Settings) -> Store | None:
    if len(token) < 40 or len(token) > 100:
        return None
    return session.scalar(
        select(Store).where(
            Store.metrics_token_hash == token_digest(token, settings), Store.is_active.is_(True)
        )
    )


def metrics_for_store(session: Session, store: Store, settings: Settings, now=None):
    zone = ZoneInfo(settings.business_timezone)
    now = now or datetime.now(zone)
    today = datetime.combine(now.astimezone(zone).date(), time.min, tzinfo=zone)
    week = today - timedelta(days=6)
    rows = session.execute(
        select(Event.event_type, func.count())
        .join(Plate, Event.plate_id == Plate.id)
        .where(Plate.store_id == store.id)
        .group_by(Event.event_type)
    ).all()
    totals = {kind.value: count for kind, count in rows}

    def views_since(start):
        return session.scalar(
            select(func.count())
            .select_from(Event)
            .join(Plate, Event.plate_id == Plate.id)
            .where(
                Plate.store_id == store.id,
                Event.event_type == EventType.PAGE_VIEW,
                Event.created_at >= start,
                Event.created_at <= now,
            )
        )

    plates = session.execute(
        select(Plate.id, Plate.name, Plate.plate_code, Plate.is_active, func.count(Event.id))
        .outerjoin(Event, (Event.plate_id == Plate.id) & (Event.event_type == EventType.PAGE_VIEW))
        .where(Plate.store_id == store.id)
        .group_by(Plate.id)
        .order_by(Plate.created_at)
    ).all()
    return {
        "store_name": store.name,
        "page_views": totals.get("page_view", 0),
        "today": views_since(today),
        "last_7_days": views_since(week),
        "google_clicks": totals.get("google_click", 0),
        "whatsapp_clicks": totals.get("whatsapp_click", 0),
        "instagram_clicks": totals.get("instagram_click", 0),
        "timezone": settings.business_timezone,
        "plates": [
            {
                "name": row.name or "Sem nome",
                "code": row.plate_code,
                "active": row.is_active,
                "page_views": row[4],
            }
            for row in plates
        ],
    }
