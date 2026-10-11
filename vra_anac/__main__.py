"""Linha de comando: a pontualidade de um mês do VRA, em texto ou JSON.

    vra-anac VRA_20267.csv --por rota --minimo 60
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vra_anac import __version__
from vra_anac.argumentos import Argumentos, nome_do_comando
from vra_anac.indicador import AGRUPAMENTOS, LIMITES_MIN, NO_HORARIO_MIN, agrupar
from vra_anac.leitura import ler_arquivo, periodo
from vra_anac.tabelas import tabelas

FONTE = ("https://www.gov.br/anac/pt-br/acesso-a-informacao/dados-abertos/areas-de-atuacao/"
         "voos-e-operacoes-aereas/voo-regular-ativo-vra")
LICENCA = "https://opendefinition.org/licenses/cc-by/"
ATRIBUICAO = f"Dados: ANAC, Voo Regular Ativo (VRA), licença CC-BY. {FONTE}"
MINIMO_PADRAO = 20
CABECALHO = {"voo": "voo", "rota": "rota", "companhia": "companhia",
             "origem": "aeroporto de origem", "destino": "aeroporto de destino"}


def _inteiro_positivo(texto: str) -> int:
    if not texto.strip().isdigit() or int(texto) < 1:
        raise argparse.ArgumentTypeError(f"precisa ser um número inteiro, 1 ou mais: {texto!r}")
    return int(texto)


def _motivo(erro: OSError, caminho: str) -> str:
    """O motivo em português, não o `strerror` do sistema."""
    if Path(caminho).is_dir():
        return "é uma pasta, não um arquivo"
    if isinstance(erro, FileNotFoundError):
        return "arquivo não encontrado"
    if isinstance(erro, PermissionError):
        return "sem permissão para ler o arquivo"
    return "não foi possível ler o arquivo"


def _milhar(n: int) -> str:
    """68355 → "68.355", como se escreve no Brasil."""
    return f"{n:,}".replace(",", ".")


def _grupo(chave, c, por, t) -> dict:
    return {
        "chave": list(chave),
        "rotulo": t.rotulo(chave, por),
        "voos": c.n,
        "chegada_no_horario_pct": c.pct("chegada"),
        "partida_no_horario_pct": c.pct("partida"),
        "cancelado_pct": c.pct("cancelado"),
        "chegada": {f.chave: f.pct for f in c.distribuicao("chegada")},
        "partida": {f.chave: f.pct for f in c.distribuicao("partida")},
    }


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        # o console do Windows (cp1252) não escreve "→": sai "?" em vez de quebrar
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")
    p = Argumentos(
        prog=nome_do_comando("vra-anac", "vra_anac"),
        description="Pontualidade dos voos domésticos regulares de um mês, pelo arquivo "
                    "do VRA da ANAC já baixado (CSV). No horário = chegada até "
                    f"{NO_HORARIO_MIN} min depois da prevista.",
        epilog=ATRIBUICAO)
    p.add_argument("arquivo", help="o CSV mensal do VRA, como baixado do site da ANAC")
    p.add_argument("--por", choices=AGRUPAMENTOS, default="voo",
                   help="agrupar por voo (padrão), rota, companhia, aeroporto de origem "
                        "ou de destino")
    p.add_argument("--minimo", type=_inteiro_positivo, default=MINIMO_PADRAO, metavar="N",
                   help=f"só os grupos com ao menos N voos no mês (padrão: {MINIMO_PADRAO})")
    p.add_argument("--json", action="store_true", help="saída em JSON, no lugar do texto")
    p.add_argument("--version", action="version", version=f"vra-anac {__version__}")
    a = p.parse_args(argv)

    try:
        atualizado, ops = ler_arquivo(a.arquivo)
        mes, fora = periodo(ops)
    except OSError as erro:
        print(f"{p.prog}: erro: {_motivo(erro, a.arquivo)}: {a.arquivo}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print(f"{p.prog}: erro: o arquivo não está em UTF-8; não parece o CSV do VRA: "
              f"{a.arquivo}", file=sys.stderr)
        return 1
    except ValueError as erro:
        print(f"{p.prog}: erro: {erro}: {a.arquivo}", file=sys.stderr)
        return 1

    t = tabelas()
    grupos = agrupar(ops, a.por, a.minimo)
    ordem = sorted(grupos.items(),
                   key=lambda kc: (-kc[1].pct("chegada"), -kc[1].n, t.rotulo(kc[0], a.por)))

    if a.json:
        print(json.dumps({
            "fonte": FONTE, "licenca": LICENCA, "atribuicao": ATRIBUICAO,
            "atualizado_em": atualizado, "mes": mes, "voos": len(ops), "fora_do_mes": fora,
            "por": a.por, "minimo": a.minimo, "no_horario_ate_min": NO_HORARIO_MIN,
            "faixas_min": list(LIMITES_MIN),
            "grupos": [_grupo(k, c, a.por, t) for k, c in ordem],
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"VRA da ANAC, {mes[5:]}/{mes[:4]} (arquivo atualizado em {atualizado}): "
          f"{_milhar(len(ops))} voos domésticos regulares"
          + (f", {fora} fora do mês" if fora else "") + ".")
    minimo = f"{a.minimo} voo{'s' if a.minimo > 1 else ''} ou mais"
    print(f"No horário = chegada até {NO_HORARIO_MIN} min depois da prevista. "
          f"Só os grupos com {minimo}.")
    print()
    if not ordem:
        print(f"Nenhum grupo com {minimo}.")
    else:
        print(f"{'no horário':>10}  {'cancelado':>9}  {'voos':>6}  {CABECALHO[a.por]}")
        for k, c in ordem:
            print(f"{c.pct('chegada'):>9}%  {c.pct('cancelado'):>8}%  {_milhar(c.n):>6}  "
                  f"{t.rotulo(k, a.por)}")
    print()
    print(ATRIBUICAO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
