"""Leitura do arquivo mensal do VRA (Voo Regular Ativo) da ANAC.

O formato foi medido em 25/09/2026, no arquivo de julho/2026:
- a 1ª linha é metadado (`Atualizado em: AAAA-MM-DD`);
- depois vem um cabeçalho com aspas, separado por `;`;
- o arquivo é UTF-8 com BOM;
- ausência vem como o TEXTO `null`, não como campo vazio.

Os horários do arquivo estão em horário de Brasília (UTC−3), também nos
aeroportos de outro fuso.
"""
from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

EMPRESA = "ICAO Empresa Aérea"
NUMERO = "Número Voo"
AUTORIZACAO = "Código Autorização (DI)"
TIPO_LINHA = "Código Tipo Linha"
ORIGEM = "ICAO Aeródromo Origem"
DESTINO = "ICAO Aeródromo Destino"
PARTIDA_PREVISTA = "Partida Prevista"
PARTIDA_REAL = "Partida Real"
CHEGADA_PREVISTA = "Chegada Prevista"
CHEGADA_REAL = "Chegada Real"
SITUACAO = "Situação Voo"

COLUNAS = (EMPRESA, NUMERO, AUTORIZACAO, TIPO_LINHA, ORIGEM, DESTINO,
           PARTIDA_PREVISTA, PARTIDA_REAL, CHEGADA_PREVISTA, CHEGADA_REAL,
           SITUACAO)

NULO = "null"
FORMATO = "%Y-%m-%d %H:%M:%S"
# Voo doméstico regular: tipo de linha N, autorização 0. Os demais códigos
# de autorização são extras e fretamentos, e só eles trazem partida
# prevista `null` (medido em julho/2026).
TIPO_DOMESTICO = "N"
AUTORIZACAO_REGULAR = "0"
SITUACOES = {"REALIZADO": False, "CANCELADO": True}


def _segundos(real: datetime | None, prevista: datetime | None) -> int | None:
    """Atraso em SEGUNDOS INTEIROS, para que 30 min exatos não virem
    30,0000001 e passem do limite."""
    if real is None or prevista is None:
        return None
    return int((real - prevista).total_seconds())


@dataclass(frozen=True)
class Operacao:
    """Um voo realizado ou cancelado, com as colunas do VRA convertidas."""
    empresa: str
    numero: str
    origem: str
    destino: str
    partida_prevista: datetime
    partida_real: datetime | None
    chegada_prevista: datetime | None
    chegada_real: datetime | None
    cancelado: bool

    @property
    def chave(self) -> tuple[str, str, str, str]:
        """O voo: empresa ICAO, número como vendido, origem e destino."""
        return (self.empresa, numero_vendido(self.numero), self.origem, self.destino)

    @property
    def atraso_partida_s(self) -> int | None:
        """Segundos da partida prevista à real (negativo = adiantou); None se cancelado."""
        return _segundos(self.partida_real, self.partida_prevista)

    @property
    def atraso_chegada_s(self) -> int | None:
        """Segundos da chegada prevista à real (negativo = adiantou); None se cancelado."""
        return _segundos(self.chegada_real, self.chegada_prevista)


def numero_vendido(numero: str) -> str:
    """'Z1001' -> '1001'.

    O Z aparece em 0,77% das operações (medido em 26/09/2026). Em 99,4%
    delas, o mesmo voo sem Z existe na mesma rota e no mesmo mês, e o
    passageiro vê o número sem a letra. A ANAC não documenta o Z: tirá-lo é
    uma inferência."""
    if numero[:1] == "Z" and numero[1:].isdigit():
        return numero[1:]
    return numero


def _instante(valor: str) -> datetime:
    """Medido em julho/2026: 6.834 horários PREVISTOS vêm com fração
    (`2026-07-17 11:00:00.100000000`, em nanossegundos) e os reais nunca.
    Um décimo de segundo não muda o atraso em minutos, então a fração é
    descartada."""
    return datetime.strptime(valor.split(".", 1)[0], FORMATO)


def _data(valor: str) -> datetime | None:
    return None if valor == NULO else _instante(valor)


def ler(texto: str) -> tuple[str, list[dict[str, str]]]:
    """Devolve (atualizado_em, linhas cruas).

    Recusa o arquivo cujo cabeçalho não traga as colunas esperadas. O
    formato de uma fonte de terceiro muda sem aviso, e ler a coluna errada
    não dá erro: dá número errado."""
    texto = texto.lstrip("﻿")
    primeira, _, resto = texto.partition("\n")
    if not primeira.startswith("Atualizado em:"):
        raise ValueError(f"1ª linha não é o metadado esperado: {primeira[:60]!r}")
    atualizado = primeira.split(":", 1)[1].strip()
    leitor = csv.DictReader(io.StringIO(resto), delimiter=";")
    faltam = [c for c in COLUNAS if c not in (leitor.fieldnames or [])]
    if faltam:
        raise ValueError(f"colunas ausentes no cabeçalho: {faltam}")
    return atualizado, list(leitor)


def regulares_domesticas(linhas: list[dict[str, str]]) -> list[Operacao]:
    """Filtra os voos domésticos regulares e converte os campos."""
    ops = []
    for n, linha in enumerate(linhas, start=3):  # 1 metadado + 1 cabeçalho
        if linha[TIPO_LINHA] != TIPO_DOMESTICO or linha[AUTORIZACAO] != AUTORIZACAO_REGULAR:
            continue
        situacao = linha[SITUACAO]
        if situacao not in SITUACOES:
            raise ValueError(f"linha {n}: situação desconhecida {situacao!r}")
        try:
            ops.append(Operacao(
                empresa=linha[EMPRESA], numero=linha[NUMERO],
                origem=linha[ORIGEM], destino=linha[DESTINO],
                partida_prevista=_instante(linha[PARTIDA_PREVISTA]),
                partida_real=_data(linha[PARTIDA_REAL]),
                chegada_prevista=_data(linha[CHEGADA_PREVISTA]),
                chegada_real=_data(linha[CHEGADA_REAL]),
                cancelado=SITUACOES[situacao],
            ))
        except ValueError as e:
            raise ValueError(f"linha {n}: data ilegível em voo regular: {e}") from e
    return ops


def ler_arquivo(caminho: str | Path) -> tuple[str, list[Operacao]]:
    """O CSV mensal baixado da ANAC: devolve (atualizado_em, voos domésticos regulares)."""
    atualizado, linhas = ler(Path(caminho).read_text(encoding="utf-8-sig"))
    return atualizado, regulares_domesticas(linhas)


def periodo(ops: list[Operacao]) -> tuple[str, int]:
    """O mês de referência sai das DATAS, não do nome do arquivo.

    Devolve o mês (AAAA-MM) mais frequente da partida prevista e quantas
    operações caem fora dele."""
    if not ops:
        raise ValueError("nenhuma operação regular doméstica no arquivo")
    meses = Counter(o.partida_prevista.strftime("%Y-%m") for o in ops)
    mes, qtd = meses.most_common(1)[0]
    return mes, len(ops) - qtd
