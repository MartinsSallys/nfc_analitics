from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.core.config import Settings
from app.core.views import templates
from app.models import Destination, Link, Plate, Store
from app.schemas.admin import LinkUpdate, PlateCreate, PlateUpdate, StoreUpdate
from app.services.metrics import rotate_metrics_token

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def find_store(session, store_id):
    store = session.get(Store, store_id)
    if store is None:
        raise HTTPException(404, "Loja não encontrada.")
    return store


def store_data(store):
    return {
        "id": str(store.id),
        "name": store.name,
        "description": store.description,
        "logo_url": store.logo_url,
        "is_active": store.is_active,
        "has_metrics_link": bool(store.metrics_token_hash),
    }


def plate_data(plate, settings):
    return {
        "id": str(plate.id),
        "name": plate.name,
        "code": plate.plate_code,
        "is_active": plate.is_active,
        "url": f"{str(settings.public_base_url).rstrip('/')}/p/{plate.plate_code}",
    }


@router.get("", response_class=HTMLResponse)
def admin_home(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={})


@router.get("/stores")
def stores(session: Session = Depends(get_db)):
    return [
        store_data(store)
        for store in session.scalars(select(Store).order_by(Store.created_at.desc()))
    ]


@router.get("/stores/{store_id}")
def detail(store_id: UUID, session: Session = Depends(get_db)):
    store = find_store(session, store_id)
    plates = session.scalars(
        select(Plate).where(Plate.store_id == store.id).order_by(Plate.created_at)
    ).all()
    links = session.scalars(select(Link).where(Link.store_id == store.id)).all()
    return {
        "store": store_data(store),
        "plates": [plate_data(p, Settings()) for p in plates],
        "links": [
            {"destination": link.destination.value, "url": link.url, "is_active": link.is_active}
            for link in links
        ],
    }


@router.put("/stores/{store_id}")
def edit_store(store_id: UUID, data: StoreUpdate, session: Session = Depends(get_db)):
    store = find_store(session, store_id)
    for key, value in data.model_dump().items():
        if key == "logo_url" and value and not value.startswith("/uploads/"):
            raise HTTPException(422, "Envie o logo pela área de upload.")
        setattr(store, key, value)
    session.commit()
    return store_data(store)


@router.post("/plates", status_code=201)
def add_plate(data: PlateCreate, session: Session = Depends(get_db)):
    find_store(session, data.store_id)
    plate = Plate(**data.model_dump())
    session.add(plate)
    session.commit()
    return plate_data(plate, Settings())


@router.patch("/plates/{plate_id}")
def edit_plate(plate_id: UUID, data: PlateUpdate, session: Session = Depends(get_db)):
    plate = session.get(Plate, plate_id)
    if plate is None:
        raise HTTPException(404, "Placa não encontrada.")
    plate.name, plate.is_active = data.name, data.is_active
    session.commit()
    return plate_data(plate, Settings())


@router.put("/stores/{store_id}/links/{destination}")
def save_link(
    store_id: UUID, destination: Destination, data: LinkUpdate, session: Session = Depends(get_db)
):
    find_store(session, store_id)
    link = session.scalar(
        select(Link).where(Link.store_id == store_id, Link.destination == destination)
    )
    if link is None:
        link = Link(store_id=store_id, destination=destination, **data.model_dump())
        session.add(link)
    else:
        link.url, link.is_active = data.url, data.is_active
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Destino alterado por outra operação. Tente novamente.") from None
    return {"destination": link.destination.value, "url": link.url, "is_active": link.is_active}


@router.post("/stores/{store_id}/metrics-token")
def metrics_token(store_id: UUID, session: Session = Depends(get_db)):
    token = rotate_metrics_token(session, find_store(session, store_id), Settings())
    return {"url": f"{str(Settings().public_base_url).rstrip('/')}/metrics/{token}"}


@router.delete("/stores/{store_id}/metrics-token", status_code=204)
def revoke_token(store_id: UUID, session: Session = Depends(get_db)):
    store = find_store(session, store_id)
    store.metrics_token_hash = None
    session.commit()


@router.post("/stores/{store_id}/logo")
async def logo(store_id: UUID, file: UploadFile, session: Session = Depends(get_db)):
    store = find_store(session, store_id)
    content = await file.read(2 * 1024 * 1024 + 1)
    await file.close()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, "A imagem deve ter no máximo 2 MB.")
    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in {"PNG", "JPEG", "WEBP"} or image.width * image.height > 16000000:
                raise ValueError()
            image.load()
            image.thumbnail((512, 512))
            output = BytesIO()
            image.convert("RGBA").save(output, format="PNG")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, "Envie uma imagem PNG, JPEG ou WebP válida.") from None
    directory = Settings().upload_dir
    directory.mkdir(parents=True, exist_ok=True)
    filename = uuid4().hex + ".png"
    path = directory / filename
    path.write_bytes(output.getvalue())
    previous = store.logo_url
    store.logo_url = f"/uploads/{filename}"
    try:
        session.commit()
    except Exception:
        session.rollback()
        path.unlink(missing_ok=True)
        raise
    if previous and previous.startswith("/uploads/"):
        old_name = previous.removeprefix("/uploads/")
        if Path(old_name).name == old_name:
            (directory / old_name).unlink(missing_ok=True)
    return {"logo_url": store.logo_url}


@router.get("/plates/{plate_id}/qr.png")
def qr(plate_id: UUID, session: Session = Depends(get_db)):
    plate = session.get(Plate, plate_id)
    if plate is None:
        raise HTTPException(404, "Placa não encontrada.")
    url = plate_data(plate, Settings())["url"]
    image = qrcode.make(url)
    output = BytesIO()
    image.save(output, format="PNG")
    return Response(
        output.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="placa-{plate.plate_code}.png"'},
    )
