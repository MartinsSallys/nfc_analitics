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
O PostgreSQL local usa a porta 15432 para evitar conflito com outros bancos.
Se alterar `POSTGRES_PORT` ou as credenciais, atualize também `DATABASE_URL`
para a execução pelo Poetry. Dentro do Compose, o banco continua usando a porta 5432.
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

## Modelo de loja

`Store` tem `id`, `name`, `description`, `logo_url`, `is_active`, `created_at` e
`updated_at`. O schema `StoreCreate` exige nome preenchido e remove espaços nas
extremidades; `StoreRead` permite representar registros consultados.
`updated_at` é preenchido na criação e atualizado nas alterações emitidas pelo
SQLAlchemy; não há trigger para alterações feitas diretamente por SQL.
A migração `0003` adiciona o campo sem apagar as lojas existentes.
O `slug` opcional foi dispensado: a URL pública usa o código da placa.
Endpoints administrativos: `POST /stores` cadastra (201); `GET /stores/{id}` consulta
(200 ou 404). Entradas inválidas retornam 422. Configure `ADMIN_USERNAME` e
`ADMIN_PASSWORD` no `.env` para usar autenticação HTTP Basic pelo botão Authorize
em `/docs`. Credenciais incorretas/ausentes retornam 401; configuração vazia
bloqueia o acesso (503). Em produção, HTTP Basic exige HTTPS. O formulário de
login e as sessões da interface administrativa ainda serão definidos.
O Compose repassa essas credenciais do `.env` ao serviço de aplicação.

## Modelo de placa

`Plate` tem `id`, `store_id`, `plate_code`, `name` opcional, `is_active`,
`created_at` e `updated_at`. O código é aleatório, único e independente do nome
da loja. O campo `updated_at` é atualizado pelo SQLAlchemy, como nas lojas.
A migração `0004` adiciona essa data preservando registros existentes.

O serviço `require_active_plate` recusa placas inexistentes ou inativas e
consulta o estado no banco mesmo quando a placa já foi carregada na sessão.
O serviço `record_event` grava os eventos iniciais previstos na issue #7 e usa
essa verificação. A migração `0005` também aplica um trigger no PostgreSQL que
bloqueia eventos de placas inativas, inclusive por SQL direto. O bloqueio usa
um lock de leitura na placa durante a gravação para coordenar desativações.
Desativar uma placa preserva os eventos anteriores. As rotas públicas de tracking
e redirects ainda serão implementadas nas respectivas issues.

## Links da loja

`Link` guarda `id`, `store_id`, `destination`, `url`, `is_active` e `created_at`.
Os destinos iniciais da issue #6 são `google`, `whatsapp` e `instagram`.
O schema `LinkCreate` e o modelo validam URLs HTTP/HTTPS e recusam URLs com
credenciais embutidas. O banco restringe os destinos e exige uma loja existente.
Os campos podem ser consultados com `LinkRead`.

Links podem ser desativados, reativados e ter sua URL alterada. Os endpoints
administrativos de links e os redirects públicos ainda não foram implementados.
A migração `0006` cria a tabela e limita cada loja a um link por destino,
inclusive se o link estiver inativo. Para trocar o endereço, edite o link existente.
Lojas diferentes podem cadastrar os mesmos tipos de destino.

## Eventos

O modelo `Event` da issue #7 foi antecipado na #5 e contém somente `id`,
`plate_id`, `event_type` e `created_at`. Não armazena IP, identificação do visitante,
user agent ou outros dados pessoais. Os tipos controlados são `page_view`,
`google_click`, `whatsapp_click` e `instagram_click`.

`record_event` verifica a placa e faz flush sem commit: o chamador decide se a
transação inteira deve ser confirmada ou revertida. Cada interação gera um novo
registro, inclusive interações repetidas. O PostgreSQL também valida tipo e vínculo.
A migração `0005` já cria essa estrutura; nenhuma migração adicional é necessária
para a revisão da issue #7. As rotas de tracking continuam nas próximas issues.
