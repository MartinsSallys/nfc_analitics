from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Verifica a aplicação, sem depender da disponibilidade do banco."""
    return {"status": "ok"}
