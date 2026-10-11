"""A pontualidade de um recorte: quantos voos chegaram no horário.

A régua do site chegounahora.com.br:
- "no horário" = chegada real até 15 min depois da prevista;
- as faixas seguintes são 16–30 min, 31–60 min e mais de 1 h;
- cancelado conta à parte, sobre o total de voos;
- a partida usa a mesma régua e fica ao lado.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

from vra_anac.leitura import Operacao, numero_vendido

NO_HORARIO_MIN = 15
LIMITES_MIN = (30, 60)
LADOS = ("chegada", "partida")
# por onde agrupar: o voo (empresa, número, origem, destino), a rota, a
# companhia, o aeroporto de origem ou o de destino
AGRUPAMENTOS = ("voo", "rota", "companhia", "origem", "destino")


def porcento(parte: int, todo: int) -> int:
    """Percentual inteiro, com o meio arredondado para cima (0,5 -> 1).

    O `round()` do Python arredonda o meio para o par, e a mesma conta
    feita à mão daria outro número."""
    if not todo:
        raise ValueError("porcentagem sobre zero operações")
    return int((Decimal(100 * parte) / Decimal(todo)).quantize(Decimal(1), ROUND_HALF_UP))


@dataclass(frozen=True)
class Fatia:
    """Uma faixa da barra.

    `pct` é o rótulo (inteiro, com o meio para cima). `largura` é o tamanho
    exato na barra, em %, com 3 casas."""
    chave: str
    voos: int
    pct: int
    largura: str


@dataclass
class Contagem:
    """Operações de um recorte, pela chegada e pela partida."""
    n: int = 0
    cancelado: int = 0
    chegada_no_horario: int = 0
    chegada_acima: dict = field(default_factory=lambda: {m: 0 for m in LIMITES_MIN})
    partida_no_horario: int = 0
    partida_acima: dict = field(default_factory=lambda: {m: 0 for m in LIMITES_MIN})

    def somar(self, op: Operacao) -> None:
        self.n += 1
        if op.cancelado:
            self.cancelado += 1
            return
        for atraso, campo_ok, campo_acima in (
                (op.atraso_chegada_s, "chegada_no_horario", self.chegada_acima),
                (op.atraso_partida_s, "partida_no_horario", self.partida_acima)):
            if atraso is None:
                # zero casos nos 12 meses medidos em 26/09/2026; se aparecer,
                # a fonte mudou e o número não pode sair calado
                raise ValueError(f"voo realizado sem horário real: {op.empresa} "
                                 f"{op.numero} {op.partida_prevista}")
            if atraso <= NO_HORARIO_MIN * 60:
                setattr(self, campo_ok, getattr(self, campo_ok) + 1)
            for m in LIMITES_MIN:
                if atraso > m * 60:
                    campo_acima[m] += 1

    def pct(self, qual: str) -> int:
        """qual: 'chegada', 'partida', 'cancelado', 'chegada>30', 'partida>60'..."""
        if qual == "cancelado":
            return porcento(self.cancelado, self.n)
        if ">" in qual:
            lado, m = qual.split(">")
            return porcento(getattr(self, f"{lado}_acima")[int(m)], self.n)
        return porcento(getattr(self, f"{qual}_no_horario"), self.n)

    def distribuicao(self, lado: str = "chegada") -> list[Fatia]:
        """O n inteiro repartido pela chegada (ou pela partida), na ordem da
        barra: no horário (até 15 min), 16–30, 31–60, mais de 1 h, cancelado."""
        realizados = self.n - self.cancelado
        ok = getattr(self, f"{lado}_no_horario")
        acima = getattr(self, f"{lado}_acima")
        a30, a60 = acima[30], acima[60]
        partes = (("no_horario", ok),
                  ("ate30", realizados - ok - a30),
                  ("ate60", a30 - a60),
                  ("acima60", a60),
                  ("cancelado", self.cancelado))
        return [Fatia(chave, voos, porcento(voos, self.n),
                      str((Decimal(100 * voos) / Decimal(self.n))
                          .quantize(Decimal("0.001"), ROUND_HALF_UP)))
                for chave, voos in partes]


def chave(op: Operacao, por: str = "voo") -> tuple[str, ...]:
    """A chave do grupo da operação. O voo usa o número sem o Z."""
    if por == "voo":
        return (op.empresa, numero_vendido(op.numero), op.origem, op.destino)
    if por == "rota":
        return (op.origem, op.destino)
    if por == "companhia":
        return (op.empresa,)
    if por == "origem":
        return (op.origem,)
    if por == "destino":
        return (op.destino,)
    raise ValueError(f"agrupamento desconhecido {por!r}: use um de {', '.join(AGRUPAMENTOS)}")


def agrupar(ops: Iterable[Operacao], por: str = "voo", minimo: int = 1) -> dict[tuple, Contagem]:
    """{chave: Contagem} dos grupos com ao menos `minimo` voos."""
    if por not in AGRUPAMENTOS:
        raise ValueError(f"agrupamento desconhecido {por!r}: use um de {', '.join(AGRUPAMENTOS)}")
    grupos: dict[tuple, Contagem] = defaultdict(Contagem)
    for op in ops:
        grupos[chave(op, por)].somar(op)
    return {k: c for k, c in grupos.items() if c.n >= minimo}
