# Publicação e operação

## Estado

A configuração é separada em `compose.prod.yaml`. Não houve deploy em VPS,
configuração de DNS ou emissão de certificado público. Esses passos dependem da
contratação da VPS e do domínio pelo responsável.

## Preparar a VPS

Use Linux com Docker e Docker Compose. Instale Docker pela documentação oficial
do seu provedor/sistema, habilite acesso SSH por chave e mantenha o sistema atualizado.
No firewall, permita SSH e as portas TCP 80/443; o PostgreSQL não tem porta pública.
Clone o repositório e acesse sua pasta.

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Edite todos os valores `SUBSTITUA`. `APP_HOST` é o domínio, sem protocolo ou caminho.
`PUBLIC_BASE_URL` é `https://` seguido desse domínio, sem caminhos adicionais.
Gere senhas com `python -c 'import secrets; print(secrets.token_hex(32))'`.
Mantenha a senha do PostgreSQL igual em `POSTGRES_PASSWORD` e `DATABASE_URL`.
Senhas hexadecimais evitam problemas de escape na URL. O host do banco é `db`.
Use uma `SECRET_KEY` exclusiva: ela protege os hashes dos tokens privados. Se for
alterada, todos os links de métricas existentes deixam de funcionar e devem ser regenerados.
Nunca versione `.env.production`; guarde uma cópia segura fora do servidor.

## Primeiro certificado

Aponte o registro A do domínio para o IPv4 da VPS. Se cadastrar AAAA, configure
IPv6 corretamente. Aguarde a propagação antes de solicitar o certificado.

O servidor temporário responde somente ao desafio de certificado, sem expor a administração:

```bash
docker compose -f deploy/compose.bootstrap.yaml up -d
```

Substitua `SEU_DOMINIO` e `SEU_EMAIL` abaixo pelos valores reais:

```bash
docker compose --env-file .env.production -f compose.prod.yaml run --rm certbot certonly --webroot -w /var/www/certbot -d SEU_DOMINIO --email SEU_EMAIL --agree-tos --no-eff-email
```

Antes de executar, leia e aceite você mesmo os termos da autoridade certificadora.
Se o desafio falhar, confira DNS, firewall e porta 80; não ignore erros de certificado.

```bash
docker compose -f deploy/compose.bootstrap.yaml down
docker compose --env-file .env.production -f compose.prod.yaml build app
docker compose --env-file .env.production -f compose.prod.yaml up -d --wait db
docker compose --env-file .env.production -f compose.prod.yaml run --rm app alembic upgrade head
docker compose --env-file .env.production -f compose.prod.yaml up -d --wait app nginx
```

O Nginx redireciona HTTP para HTTPS. FastAPI e PostgreSQL ficam na rede interna.
A aplicação roda sem root e com sistema de arquivos somente leitura, exceto uploads e `/tmp`.
`/docs`, `/redoc` e OpenAPI são desativados em produção.

## Atualizações

Faça backup antes de atualizar. Após revisar o novo código:

```bash
git pull --ff-only
docker compose --env-file .env.production -f compose.prod.yaml build app
docker compose --env-file .env.production -f compose.prod.yaml run --rm app alembic upgrade head
docker compose --env-file .env.production -f compose.prod.yaml up -d --wait app nginx
```

Não use `down -v`: isso apaga os dados. Reverter imagem não reverte migrações;
revise compatibilidade e backup antes de qualquer rollback de banco.

## Renovação de HTTPS

Configure na VPS uma execução diária do comando abaixo e acompanhe falhas. Isso
não foi agendado automaticamente neste projeto.

```bash
docker compose --env-file .env.production -f compose.prod.yaml run --rm certbot renew --webroot -w /var/www/certbot
docker compose --env-file .env.production -f compose.prod.yaml exec -T nginx nginx -s reload
```

Depois da primeira publicação, teste também `certbot renew --dry-run`.

## Backup e restauração

Execute diariamente e antes de atualizações:

```bash
bash scripts/backup.sh
```

O script salva um dump PostgreSQL e um arquivo dos logos em `backups/`.
Copie ambos para armazenamento fora da VPS e defina retenção (por exemplo, 7 diários
e 4 semanais). Volume persistente e snapshot do provedor não substituem essa cópia.
Tokens privados são armazenados somente como hash, mas dumps continuam sendo dados privados.

Para restaurar, prepare um banco vazio separado e uma cópia dos uploads. Teste a
restauração sem substituir o banco de produção. A estrutura do dump é `pg_dump -Fc`;
use `pg_restore` com o mesmo PostgreSQL 17 e a configuração correspondente. Não rode
comandos de limpeza/restauração destrutivos no banco real sem uma janela de manutenção.
O teste de restauração está descrito no relatório de validação local.

## Verificações após deploy

- HTTPS com certificado público válido e HTTP redirecionando.
- `/health` retorna 200; não é prova de que o banco esteja disponível.
- Administração exige as credenciais reais e recusa credenciais inválidas.
- Cadastrar loja piloto, abrir uma placa e conferir incremento nas métricas.
- Clicar nos três destinos e conferir destino e contagem.
- Desativar placa/link e conferir bloqueio.
- Rotacionar token e confirmar que o antigo retorna 404.
- Reiniciar serviços e conferir persistência de banco e logos.

Os dados de demonstração não devem ser criados em produção.
