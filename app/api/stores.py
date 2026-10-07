from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.schemas.store import StoreCreate, StoreRead
from app.services.stores import create_store, get_store

router = APIRouter(prefix="/stores", tags=["stores"], dependencies=[Depends(require_admin)])


@router.post("", response_model=StoreRead, status_code=201)
def create(data: StoreCreate, response: Response, session: Session = Depends(get_db)):
    store = create_store(session, data)
    response.headers["Location"] = f"/stores/{store.id}"
    return store


@router.get("/{store_id}", response_model=StoreRead)
def retrieve(store_id: UUID, session: Session = Depends(get_db)):
    store = get_store(session, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Loja não encontrada.")
    return store
