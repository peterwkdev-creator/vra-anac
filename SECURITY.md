# Segurança

## Como avisar

Falha de segurança não vai em issue pública: use o aviso privado do GitHub,
em [Security → Report a vulnerability](https://github.com/peterwkdev-creator/vra-anac/security/advisories/new).
Diga a versão, o passo a passo para reproduzir e o efeito.

## O que esperar

- Primeira resposta em até 14 dias.
- A correção sai na última versão publicada; versões antigas não recebem
  correção.
- Crédito no [CHANGELOG.md](CHANGELOG.md) e no aviso, se você quiser.

## O que não é falha de segurança

Resultado diferente do esperado (um valor, uma regra, um caso que falta) é
issue comum, pelo modelo "Resultado diferente do esperado".
A biblioteca só lê o CSV que você indicar: não acessa a rede, não grava
arquivo e não tem dependências.
