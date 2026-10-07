# Escopo do MVP — NFC Analytics

Status: escopo aprovado para orientar a implementação.

## Objetivo

Permitir que uma loja ofereça uma página pública acessível por NFC ou QR Code e acompanhe os acessos à placa e os cliques nos destinos cadastrados.

## Fluxo principal

1. O visitante aproxima o celular da placa NFC ou lê o QR Code.
2. O celular abre `/p/{plate_code}`.
3. O sistema valida a placa e registra o acesso, com data e hora.
4. O sistema exibe a página pública da loja com seus destinos ativos.
5. O visitante escolhe um destino.
6. O sistema recebe `/r/{plate_code}/{destination}`, valida a placa e o destino e registra o clique.
7. O sistema redireciona para a URL cadastrada usando HTTP 302.

O visitante não precisa criar conta. Se a placa ou o destino estiverem inexistentes ou desativados, o sistema exibe uma mensagem de indisponibilidade e não contabiliza o evento correspondente.

## Funcionalidades incluídas

- NFC e QR Code apontando para a mesma URL pública da placa.
- Cadastro básico de loja: nome, descrição curta e logo opcional.
- Cadastro de placa com código único e vínculo com uma loja.
- Uma loja pode ter várias placas; cada placa pertence a uma única loja.
- Configuração de destinos da loja, como WhatsApp, Instagram, localização e site.
- Página pública responsiva com os destinos ativos.
- Registro de acessos por placa, com data e hora.
- Registro de cliques por placa e destino, com data e hora.
- Área administrativa protegida por login exclusivo do responsável pelo projeto para gerenciar lojas, placas e destinos.
- Visualização simples dos totais de acessos e cliques por placa e destino.
- Consulta das métricas de cada loja por link privado com token aleatório, sem login e sem edição; o administrador pode revogar e gerar outro link.

## URL pública da placa

Padrão: `https://{dominio}/p/{plate_code}`.

Exemplo: `/p/a7k9m2`.

- O código é único, não sequencial e estável.
- NFC e QR Code usam a mesma URL.
- Alterar destinos não altera a URL da placa.
- Placas inexistentes ou desativadas não geram acesso contabilizado.

## Redirects rastreáveis

Padrão: `https://{dominio}/r/{plate_code}/{destination}`.

Exemplos:

- `/r/a7k9m2/whatsapp`
- `/r/a7k9m2/instagram`
- `/r/a7k9m2/maps`
- `/r/a7k9m2/site`

`destination` é uma chave estável do destino cadastrado para a loja, não uma URL externa. Os exemplos ilustram as chaves; não exigem que toda loja tenha todos esses destinos.

O sistema valida se a placa e o destino estão ativos, busca a URL no cadastro, registra o clique antes de redirecionar e responde com HTTP 302. Não aceita URLs externas arbitrárias enviadas pelo visitante. Destinos inválidos não geram clique contabilizado.

## Regras de medição

- Acessos e cliques são eventos separados.
- Recarregar a página gera um novo acesso.
- Clicar novamente gera um novo clique.
- Os totais representam eventos, não pessoas únicas.
- O MVP não diferencia NFC de QR Code, porque usam a mesma URL.
- Não há promessa de filtragem avançada de bots ou identificação de visitantes únicos.

## Fora do MVP

- Pagamento automático.
- Assinatura.
- Inteligência artificial.
- Relatórios PDF.
- Aplicativo mobile.
- Dashboard avançado.
- Múltiplos planos.
- Personalização livre de layout.
- Rastreamento de ações depois do redirecionamento, como compras ou mensagens enviadas.
- Identificação de visitantes únicos e atribuição avançada.

## Critérios de aceite desta issue

- [x] Fluxo principal documentado.
- [x] Funcionalidades do MVP definidas.
- [x] Funcionalidades fora do MVP definidas.
- [x] Padrão da URL pública da placa definido.
- [x] Padrão dos redirects rastreáveis definido.
- [x] Comportamento de placas e destinos inválidos definido.
- [x] Regras de contagem e limitações documentadas.

Esses critérios verificam a definição do escopo, não a implementação das funcionalidades.

## Próximas decisões

A stack e o modelo de acesso estão definidos em [Stack aprovada](stack.md). Domínio, provedor e plano da VPS serão decididos ao final do desenvolvimento local. Decisões de implementação e mudanças de escopo continuam com o responsável pelo projeto.
