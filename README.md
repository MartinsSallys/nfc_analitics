# NFC Analytics

Página pública de lojas acessível por NFC ou QR Code, com registro de acessos e cliques por placa.

## Documentação

- [Escopo do MVP](docs/escopo-mvp.md): fluxo principal, funcionalidades incluídas, exclusões, URLs e regras de medição.

- [Stack aprovada](docs/stack.md): tecnologias, acesso administrativo, links privados e planejamento de hospedagem.

## Estado do projeto

Escopo do MVP e stack documentados. Base técnica criada. Funcionalidades de lojas, placas, métricas e login ainda não implementadas.


## Executar localmente

Requisitos: Python 3.12 a 3.14, Poetry 2.4 e Docker com Compose.

```bash
cp .env.example .env
poetry install
# Apenas PostgreSQL em container e aplicação pelo Poetry:
docker compose up -d db
poetry run uvicorn app.main:app --reload
```

Alternativamente, execute aplicação e banco em containers:

```bash
docker compose up --build -d
```

Use apenas uma das formas para a aplicação, pois ambas usam a porta 8000.
Abra http://localhost:8000/health para verificar a resposta e
http://localhost:8000/docs para consultar as rotas.
A rota de saúde verifica somente a aplicação; não garante conexão com o banco.

## Verificações

```bash
poetry run ruff check .
poetry run ruff format --check .
```

pytest e HTTPX estão instalados para os testes das próximas funcionalidades.
Alembic está instalado; suas migrações serão configuradas com os primeiros modelos.

## Banco e configuração

`.env.example` contém credenciais exclusivamente locais. `.env` não é versionado.
Se alterar as credenciais locais, atualize também `DATABASE_URL` para a execução pelo Poetry.
O Compose usa o host `db` para a conexão da aplicação em container.
O banco guarda os dados em um volume. `docker compose down` preserva esse volume;
`docker compose down -v` apaga os dados locais.
A configuração atual é para desenvolvimento; o deploy na VPS será preparado posteriormente.
