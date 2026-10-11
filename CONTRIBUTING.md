# Como contribuir

Resultado diferente do esperado ou caso que falta: abra uma issue pelo
modelo "Resultado diferente do esperado". Para mandar código:

- Os testes rodam do checkout, sem instalar nada:

  ```bash
  python -m unittest
  ```

- Só a biblioteca padrão: nenhuma dependência.
- Valor novo (companhia, aeroporto, regra de leitura) cita a fonte e a
  data da consulta; tabela nova tem a fonte em cada linha.
- Todo caso novo tem teste, com o resultado esperado escrito à mão no
  próprio teste.
- Exemplos e testes com linhas reais do VRA (dado aberto da ANAC, CC-BY),
  copiadas sem alteração, ou com voos inventados; nada de dado pessoal.
- Código, mensagens e documentação em português do Brasil.
- Mudança de comportamento entra no [CHANGELOG.md](CHANGELOG.md).
- Código próprio: não traga código copiado de outro projeto, mesmo de
  licença livre. O que você contribui sai sob a [licença MIT](LICENSE) do
  projeto.
