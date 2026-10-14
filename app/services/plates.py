from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Plate


class PlateUnavailableError(Exception):
    """Placa inexistente ou inativa, indisponível para novos eventos."""


def require_active_plate(session: Session, plate_code: str) -> Plate:
    """Consulta a situação atual da placa antes do futuro registro de eventos."""
    plate = session.scalar(
        select(Plate)
        .where(Plate.plate_code == plate_code, Plate.is_active.is_(True))
        .execution_options(populate_existing=True)
    )
    if plate is None:
        raise PlateUnavailableError("Placa indisponível.")
    return plate
