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
poetry run pytest
poetry run ruff check .
poetry run ruff format --check .
```

Os testes verificam saúde, configuração, persistência de lojas e placas,
restrições do PostgreSQL e reversão/reaplicação das migrações.
É necessário Docker em execução para rodar a suíte completa. Os testes criam
um PostgreSQL 17 descartável em porta aleatória e removem o container ao terminar;
não usam o banco de desenvolvimento nem o `DATABASE_URL` do seu `.env`.
Para rodar apenas os testes sem banco:

```bash
poetry run pytest tests/test_health.py tests/test_config.py
```
HTTPX usa ASGITransport diretamente, evitando o aviso de descontinuação do TestClient.
Alembic está configurado. Para criar/atualizar as tabelas com o banco local iniciado:

```bash
poetry run alembic upgrade head
poetry run alembic current
```

Se estiver usando aplicação e banco em containers:

```bash
docker compose exec app alembic upgrade head
```

A primeira migração cria `stores`; a segunda cria `plates`, com vínculo obrigatório
à loja e código público único. O código é gerado pelo Python ao salvar e não deve
ser alterado nos futuros endpoints de edição. Novas alterações serão adicionadas como novas
migrações; a aplicação não cria tabelas automaticamente ao iniciar.

## Banco e configuração

`.env.example` contém credenciais exclusivamente locais. `.env` não é versionado.
Se alterar as credenciais locais, atualize também `DATABASE_URL` para a execução pelo Poetry.
O Compose usa o host `db` para a conexão da aplicação em container.
O banco guarda os dados em um volume. `docker compose down` preserva esse volume;
`docker compose down -v` apaga os dados locais.
A configuração atual é para desenvolvimento; o deploy na VPS será preparado posteriormente.

## Estrutura

```text
app/
  main.py       # Criação da aplicação
  api/          # Rotas HTTP
  core/         # Configuração e conexão com o banco
  models/       # Modelos de persistência
  schemas/      # Dados de entrada e saída
  services/     # Regras de negócio
  templates/    # Páginas Jinja2
  static/       # CSS, JavaScript e imagens
tests/         # Testes automatizados
```

As pastas de funcionalidades estão preparadas; seus modelos e regras serão
implementados nas próximas issues. Para verificar apenas a aplicação, é possível
executar Uvicorn sem iniciar o PostgreSQL.
