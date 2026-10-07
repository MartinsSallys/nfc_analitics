from fastapi import FastAPI

app = FastAPI(title="NFC Analytics", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Verifica se a aplicação responde; não verifica a conexão com o banco."""
    return {"status": "ok"}
