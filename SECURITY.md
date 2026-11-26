# Política de segurança

## Reportando uma vulnerabilidade

Use a aba [Security](https://github.com/EduardoSFragoso/laro_mvp_tracker/security)
→ **Report a vulnerability** para abrir um canal privado com os mantenedores.
Esse recurso precisa estar ativo nas configurações do repositório. Se o botão
não aparecer, contate o mantenedor por um canal privado conhecido.

Por favor, **não abra uma issue pública** descrevendo falhas de segurança.

## Escopo

- Código do bot (`src/laro/`) e a imagem Docker que o empacota.
- Configuração de deploy versionada (`docker-compose.yml`, CI).
- Não está no escopo: a infraestrutura de produção (VM, banco, tokens),
  que não é pública.

## O que esperar

- Confirmação de recebimento em até 7 dias.
- Correção priorizada conforme a gravidade; este é um projeto de tempo livre,
  portanto prazos exatos não são prometidos.
- A pessoa que reportar será creditada na descrição da correção, se desejar.

## Boas práticas ao reportar

- Descreva o impacto e os passos para reproduzir.
- Não teste a vulnerabilidade contra o bot em produção além do necessário
  para demonstrá-la.
