"""Cria uma loja fictícia local. Não usar como cadastro da loja piloto real."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.core.database import create_session_factory  # noqa: E402
from app.models import Destination, Link, Plate, Store  # noqa: E402
from app.services.metrics import rotate_metrics_token  # noqa: E402

settings = Settings()
if settings.environment == "production":
    raise SystemExit("A demonstração só pode ser criada fora de produção.")
factory = create_session_factory(settings)
with factory() as session:
    store = session.scalar(select(Store).where(Store.name == "Loja Demonstração NFC"))
    if store is None:
        store = Store(name="Loja Demonstração NFC", description="Seu próximo contato começa aqui.")
        session.add(store)
        session.flush()
        for kind in Destination:
            session.add(
                Link(store_id=store.id, destination=kind, url=f"https://example.com/{kind.value}")
            )
        session.add(Plate(store_id=store.id, name="Balcão de demonstração"))
        session.commit()
    plate = session.scalar(select(Plate).where(Plate.store_id == store.id))
    token = rotate_metrics_token(session, store, settings)
    base = str(settings.public_base_url).rstrip("/")
    print(f"Página: {base}/p/{plate.plate_code}")
    print(f"Métricas (link privado, não publicar): {base}/metrics/{token}")
    print(f"Administração: {base}/admin")
