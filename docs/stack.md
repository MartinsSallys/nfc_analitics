# Stack aprovada — NFC Analytics

## Tecnologias

| Parte | Escolha | Papel |
|---|---|---|
| Linguagem | Python | Backend |
| Dependências | Poetry | Ambiente e dependências |
| Aplicação web | FastAPI | Rotas e processamento das requisições |
| Interface | HTML, CSS, JavaScript e Jinja2 | Página pública, painel e métricas |
| Validação | Pydantic | Validação dos dados |
| Acesso ao banco | SQLAlchemy 2.x | Modelos, consultas e transações |
| Banco | PostgreSQL | Persistência dos dados |
| Driver | Psycopg 3 | Comunicação do Python com PostgreSQL |
| Migrações | Alembic | Histórico de alterações das tabelas |
| Testes | pytest e HTTPX/TestClient | Verificação das regras e rotas |
| Qualidade do código | Ruff | Formatação e análise |
| Containers | Docker e Docker Compose | Aplicação e banco em serviços separados |

Acesso ao banco: FastAPI → SQLAlchemy → Psycopg 3 → PostgreSQL.

## Acesso ao sistema

- Apenas o responsável pelo projeto terá login administrativo.
- O administrador gerencia lojas, placas, destinos e links de métricas.
- Cada loja consulta somente suas métricas por link privado, sem login e sem edição.
- O link usa token longo e aleatório, independente do código público da placa.
- O administrador pode revogar o link e gerar outro.
- Quem possui o link pode consultar as métricas da loja vinculada.
- Em produção, usar HTTPS, proteger o token nos logs e evitar recursos externos na página de métricas que possam receber o link.

## Desenvolvimento e hospedagem

- Desenvolvimento local com PostgreSQL em container.
- Aplicação e banco em containers separados, coordenados por Docker Compose.
- Dados do PostgreSQL em volume persistente; volume não substitui backup.
- Planejamento de produção em VPS Linux.
- Provedor, plano, RAM, domínio e contratação serão decididos ao final do desenvolvimento local.
- Orçamento informado: R$ 50 mensais. Nenhum serviço contratado nesta etapa.

## Decisões de implementação pendentes

Versões exatas, mecanismo de sessão administrativa, armazenamento de logos, estratégia de backup e configuração de deploy serão definidos nas respectivas etapas. Esta aprovação não instala dependências nem implementa funcionalidades.
