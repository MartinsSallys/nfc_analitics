# Validação do MVP em ambiente local

Data: 17/10/2026.

## Concluído

- Suíte com PostgreSQL 17 descartável: 103 testes passaram.
- Ruff, formatação, sintaxe do JavaScript e do script de backup verificadas.
- Migrações aplicadas ao banco de desenvolvimento até 0007; Alembic sem diferenças.
- Página pública e métricas revisadas no navegador em 320/390 px e desktop 1280 px.
- Sem rolagem lateral da página; tabela de métricas ajustada para 320 px.
- Botões públicos com altura de 64 px e foco de teclado visível.
- Administração testada no navegador: cadastro de loja fictícia, canal e placa.
- Console sem erros na revisão dos formulários.

## Simulação de produção

Containers isolados: PostgreSQL, aplicação Python 3.12 e Nginx, publicados somente
em loopback. Certificado TLS temporário local, validado com sua própria CA no cliente
de teste. Isso não é certificado público nem teste de domínio real.

Verificados:

- Construção da imagem, inicialização saudável e `nginx -t`.
- Configuração de produção, documentação desativada e credenciais obrigatórias.
- Cadastro, placa, canais, página pública, redirect e contagens.
- QR Code PNG e upload validado de imagem.
- Consulta privada e revogação do token anterior.
- Token privado ausente dos logs da aplicação e Nginx.
- Persistência de banco e logo depois do reinício da aplicação.
- Dump restaurado em um banco separado, com a mesma quantidade de lojas.
- Arquivo de backup dos uploads extraído e presença do logo confirmada.

O teste de produção encontrou e corrigiu permissões SELinux dos mounts do Nginx.
Os serviços e volumes descartáveis da simulação são removidos ao terminar;
o banco de desenvolvimento é preservado.

## Evidência visual

- [Página pública no celular](screenshots/public-mobile.jpg)
- [Métricas no celular](screenshots/metrics-mobile.jpg)
- [Métricas no desktop](screenshots/metrics-desktop.jpg)
- [Administração no desktop](screenshots/admin-desktop.jpg)

As capturas usam lojas e eventos fictícios.

## Não verificado externamente

- CI no GitHub: consultar o resultado da execução do workflow após o push.
- VPS real, domínio/DNS e certificado público.
- Leitura de QR e NFC em celulares reais.
- Uso por uma pessoa externa e feedback da loja piloto.

Essas etapas permanecem abertas nas issues correspondentes. Não há evidência de
entrega física ou uso em produção.
