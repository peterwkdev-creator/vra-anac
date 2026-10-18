# vra-anac

[![testes](https://github.com/peterwkdev-creator/vra-anac/actions/workflows/testes.yml/badge.svg)](https://github.com/peterwkdev-creator/vra-anac/actions/workflows/testes.yml)
[![PyPI](https://img.shields.io/pypi/v/vra-anac?label=PyPI)](https://pypi.org/project/vra-anac/)
[![Python](https://img.shields.io/pypi/pyversions/vra-anac?label=Python)](https://pypi.org/project/vra-anac/)
[![licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue)](https://github.com/peterwkdev-creator/vra-anac/blob/main/LICENSE)

Quantos voos domésticos chegaram no horário, por voo, rota, companhia ou
aeroporto, a partir do arquivo mensal do **VRA (Voo Regular Ativo) da
ANAC**. Lê o CSV como a ANAC publica e aplica a mesma régua do
[chegounahora.com.br](https://chegounahora.com.br/): **no horário = chegada
até 15 min depois da prevista**.

Só a biblioteca padrão do Python, sem rede: você baixa o CSV, ela faz a conta.

![O comando vra-anac lê o CSV de agosto/2026 da ANAC e mostra a pontualidade por companhia e por rota](https://raw.githubusercontent.com/peterwkdev-creator/vra-anac/main/docs/vitrine.gif)

## Instalar

```bash
pip install vra-anac
```

Ou uma versão exata, pela tag do GitHub:

```bash
pip install "git+https://github.com/peterwkdev-creator/vra-anac@v0.1.0"
```

Python 3.11 ou mais novo.

## Usar

```python
import vra_anac

# o CSV do mês que você baixou da ANAC (aqui, a amostra dos testes)
atualizado, voos = vra_anac.ler_arquivo("tests/fixtures/vra-amostra.csv")
t = vra_anac.tabelas()

for chave, c in vra_anac.agrupar(voos, por="voo").items():
    print(f"{t.rotulo(chave)}: {c.pct('chegada')}% no horário (n = {c.n})")
# G3 1015 SDU→CGH: 100% no horário (n = 1)
# G3 1016 CGH→SDU: 0% no horário (n = 2)
# ...
```

Pela linha de comando, a tabela do mês (ou `--json`):

```bash
vra-anac VRA_20268.csv --por companhia
```

```
VRA da ANAC, 08/2026 (arquivo atualizado em 2026-10-07): 68.355 voos domésticos regulares, 1 fora do mês.
No horário = chegada até 15 min depois da prevista. Só os grupos com 20 voos ou mais.

no horário  cancelado    voos  companhia
       87%         1%  23.080  Azul (AZU)
       84%         2%  20.295  GOL (GLO)
       78%         1%  23.850  LATAM (TAM)
       76%        16%   1.098  Azul Conecta (ACN)
        0%       100%      24  Apuí Táxi Aéreo (CQB)

Dados: ANAC, Voo Regular Ativo (VRA), licença CC-BY. https://www.gov.br/anac/...
```

`--por` aceita `voo` (padrão), `rota`, `companhia`, `origem` e `destino`;
`--minimo` (padrão 20) deixa de fora o grupo com poucos voos, que oscila por
acaso de um mês para o outro.

## Onde baixar o CSV

Na página do [Voo Regular Ativo (VRA)](https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/voo-regular-ativo-vra)
da ANAC, um arquivo por mês (`VRA_AAAAM.csv`, o mês sem zero). A ANAC
publica com cerca de 4 semanas de atraso.

## O que a conta faz

- **Voo doméstico regular**: tipo de linha `N` e código de autorização `0`.
  Extras, fretamentos e voos internacionais ficam de fora.
- **No horário**: chegada real até 15 min depois da prevista; adiantado
  conta como no horário. A partida tem o mesmo critério, ao lado
  (`c.pct("partida")`).
- **Faixas**: até 30 min, até 60 min, mais de 60 min e cancelado
  (`c.distribuicao("chegada")`). O atraso é contado em segundos inteiros:
  30 min exatos ficam na faixa de até 30.
- **Cancelado** conta no total e nunca como no horário.
- **Porcentagem** arredondada com o meio para cima (12,5 → 13).
- **O voo** é empresa + número + origem + destino. O número sai sem o `Z`
  que o VRA às vezes põe na frente (`Z1001` e `1001` são o mesmo voo
  vendido). Isso é inferência, conferida em alguns voos contra o horário
  publicado pela companhia, não regra escrita da ANAC.
- **O mês** sai das datas das linhas, não do nome do arquivo; o que cai em
  outro mês aparece contado à parte (`vra_anac.periodo`).
- Os horários são os do arquivo, em Brasília.

## O que vem junto

As tabelas que levam o código ICAO do VRA ao que aparece no bilhete
(`GLO` → `G3`, `SBSP` → `CGH Congonhas`): companhias do cadastro da ANAC e
do diretório da IATA, e aeroportos da lista de aeródromos públicos da ANAC
e do OurAirports (domínio público). Cada linha cita a fonte e a data da
consulta (`t.companhias`, `t.aeroportos`). Código fora da tabela aparece
como veio no arquivo.

## Como é testado

`python -m unittest`, do checkout, sem instalar nada. A amostra dos testes
tem linhas reais do VRA de julho/2026, com os bytes do arquivo da ANAC (BOM
e CRLF), e cada número esperado foi contado à mão. O CI roda do Python 3.11
ao 3.14 e no Windows, e instala o pacote num ambiente limpo antes de cada
versão.

## Fontes e limites

- **Dados: ANAC, Voo Regular Ativo (VRA), licença
  [CC-BY](https://opendefinition.org/licenses/cc-by/).** Quem publicar
  resultado feito com esta biblioteca precisa dar o crédito à ANAC; a linha
  de comando já escreve a atribuição na saída.
- Esta biblioteca **não é da ANAC** nem de companhia aérea. O resultado
  mostra o que aconteceu no mês, não prevê o próximo voo.
- O VRA não traz o motivo do atraso (o campo de justificativa vem vazio).

## Contribuir

Ver o [CONTRIBUTING.md](https://github.com/peterwkdev-creator/vra-anac/blob/main/CONTRIBUTING.md).
Resultado diferente da sua conta: abra uma issue pelo modelo "Resultado
diferente do esperado".

<!-- outros-projetos:inicio -->
## Outros projetos

| Projeto | Para que serve |
|---|---|
| [numeros-publicos](https://github.com/peterwkdev-creator/numeros-publicos) · [site](https://www.numerospublicos.com.br) | Dados abertos de cada município brasileiro (IBGE, Tesouro Nacional, INEP), conferidos contra a fonte, uma página por município |
| [simples-nacional-br](https://github.com/peterwkdev-creator/simples-nacional-br) · [site](https://peterwkdev-creator.github.io/simples-nacional-br/) | Simples Nacional conferido contra a LC 123 e a LC 214: alíquota, DAS, repartição, Fator R e CNAE |
| [linguagem-simples-br](https://github.com/peterwkdev-creator/linguagem-simples-br) · [site](https://peterwkdev-creator.github.io/linguagem-simples-br/) | Verificador aberto da Lei 15.263/2025 (Linguagem Simples): confere um texto contra o art. 5º |
| [claude-context-cost](https://github.com/peterwkdev-creator/claude-context-cost) · [site](https://peterwkdev-creator.github.io/claude-context-cost/) | Quanto cada fonte (CLAUDE.md, regras, skills, memória) custa no contexto de uma sessão do Claude Code |
| [numerasheets-site](https://github.com/peterwkdev-creator/numerasheets-site) · [site](https://numerasheets.com) | Vitrine da loja NumeraSheets: modelos de planilha e calculadoras grátis |
| [kerbo-releases](https://github.com/peterwkdev-creator/kerbo-releases) | Versões assinadas do Kerbo, segunda opinião de segurança, rede e disco no Windows |
<!-- outros-projetos:fim -->

## Licença

Código sob a [licença MIT](https://github.com/peterwkdev-creator/vra-anac/blob/main/LICENSE).
Os dados do VRA são da ANAC, sob CC-BY.
