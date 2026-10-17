# NFC Analytics

MVP para lojas com página pública via NFC/QR, cliques rastreáveis e métricas privadas.

## Fluxo

`NFC/QR → /p/{plate_code} → visita → canais da loja → /r/{plate_code}/{destination} → clique → HTTP 302`

- Página pública sem login, com nome, descrição e logo opcional.
- Google, WhatsApp e Instagram: um link por destino por loja.
- Placas e lojas inativas não geram novos eventos pelo fluxo público.
- Administração exclusiva do responsável, por autenticação HTTP Basic.
- Loja consulta apenas suas métricas por link privado, sem login ou edição.
- Link privado revogável: somente seu hash fica no banco.
- QR Code PNG com a mesma URL da NFC.

## Rodar localmente

Python 3.12–3.14, Poetry 2.4 e Docker com Compose.

```bash
cp .env.example .env
poetry install
```

Preencha `ADMIN_USERNAME` e `ADMIN_PASSWORD` no `.env`. Para gerar uma senha:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(24))'
```

```bash
docker compose up -d --wait db
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --no-access-log
```

Abra [Administração](http://localhost:8000/admin) e informe as credenciais do `.env`.
O navegador apresenta a autenticação básica; não há conta ou senha para o lojista.

Se a porta 8000 estiver ocupada, inicie com `--port 18002` e ajuste
`PUBLIC_BASE_URL=http://localhost:18002` no `.env`. O banco local usa 15432;
se alterar `POSTGRES_PORT`, atualize também `DATABASE_URL`.

Alternativa: aplicação e banco em containers:

```bash
docker compose up --build -d --wait
docker compose exec app alembic upgrade head
```

Não execute as duas formas na mesma porta. Os arquivos de logo ficam em volume
persistente no Compose; no modo Poetry, ficam em `uploads/`, ignorado pelo Git.
Alterar `.env` exige reiniciar a aplicação; recrie o serviço no Compose.

## Teste com loja fictícia

```bash
poetry run python scripts/demo.py
```

O script cria uma loja de demonstração e imprime as URLs pública e privada.
Os canais apontam para `example.com`. Cada execução gera um novo link de métricas
e invalida o anterior. Não cadastrar essa loja como piloto real.

## Operação administrativa

1. Cadastre a loja em `/admin`.
2. Configure as URLs completas dos três canais; desative canais não usados.
3. Envie o logo PNG/JPEG/WebP (até 2 MB), se houver.
4. Crie a placa, com nome opcional como “Balcão”.
5. Baixe o QR Code e use a mesma URL pública para gravar a NFC.
6. Gere o link de métricas e copie-o: ele só aparece nessa operação.
7. Envie o link à loja por um canal escolhido por você. Quem o possui pode consultar as métricas.

É possível editar loja/canais, ativar e desativar placas e revogar o acesso às métricas.
A URL da placa não muda ao editar a loja ou os canais.

## Métricas

Acessos totais, hoje, últimos 7 dias, cliques por destino e acessos por placa.
O período de 7 dias inclui hoje e os seis dias anteriores, no fuso
`America/Fortaleza`. Eventos repetidos contam separadamente; não são visitantes únicos.
NFC e QR usam a mesma URL, portanto não são diferenciados.

Não coletamos IP, user agent ou identificação de visitantes nos eventos.
URLs com tokens privados não devem aparecer nos logs. Access logs do Uvicorn
são desativados; o log da aplicação usa o padrão da rota, como `/metrics/{token}`.
O Nginx de produção também não registra access logs.

## Testes

```bash
poetry run pytest -q
poetry run ruff check .
poetry run ruff format --check .
```

A suíte cria um PostgreSQL 17 descartável em porta aleatória e remove-o ao terminar.
Não usa nem apaga o banco de desenvolvimento. É necessário Docker ativo.
A CI executa os mesmos testes com Python 3.12.

## Estrutura

- `app/api/`: endpoints públicos, administrativos e métricas.
- `app/core/`: configuração, banco, templates e cabeçalhos.
- `app/models/`: lojas, placas, links e eventos.
- `app/schemas/`: validação de entradas e respostas.
- `app/services/`: regras de tracking e consulta privada.
- `app/templates/`, `app/static/`: interface Jinja2 e arquivos locais.
- `migrations/`: histórico Alembic; não altere migrações já aplicadas.
- `tests/`: testes com PostgreSQL real isolado.

`created_at` é preenchido pelo banco. `updated_at` em lojas e placas é atualizado
pelo SQLAlchemy; alterações por SQL direto precisam atualizar o campo explicitamente.
O PostgreSQL rejeita eventos para placas inativas e códigos/destinos duplicados.
Schemas validam URLs e nome da loja antes das operações da aplicação.

## Documentação e estado

- [Escopo aprovado](docs/escopo-mvp.md)
- [Stack aprovada](docs/stack.md)
- [Publicação, HTTPS e backup](docs/producao.md)
- [Roteiro do piloto e pendências reais](docs/piloto.md)
- [Relatório de validação local](docs/validacao-local.md)

Aplicação preparada para validação local. A entrega em produção depende de VPS,
domínio e teste físico com QR/NFC. Não confundir testes locais com publicação.
