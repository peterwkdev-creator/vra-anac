"""Do código ICAO do VRA ao rótulo que o passageiro conhece (G3 1044, CGH).

A chave de tudo é o código ICAO lido das colunas do VRA. As tabelas só dão
o rótulo, e cada linha traz a fonte:
- `companhias.csv`: o código com que o voo é VENDIDO (`iata`), que nem
  sempre é o do cadastro (`iata_registro_anac`). A LATAM tem o cadastro JJ
  e vende como LA desde 11/05/2018; a Azul Conecta vende com o AD da Azul.
- `aeroportos.csv`: IATA, nome curto, nome oficial, município, UF e fuso.
  Nome, município e UF vêm das listas de aeródromos da ANAC; o IATA, do
  OurAirports (domínio público), conferido no diretório da IATA.

Montadas em 26/09/2026. Código que não está na tabela sai como veio (ICAO).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files


@dataclass(frozen=True)
class Tabelas:
    companhias: dict
    aeroportos: dict

    def companhia(self, icao: str) -> dict:
        """A linha da tabela; ValueError se o código não estiver nela."""
        try:
            return self.companhias[icao]
        except KeyError:
            raise ValueError(f"companhia {icao} sem tradução na tabela") from None

    def aeroporto(self, icao: str) -> dict:
        """A linha da tabela; ValueError se o código não estiver nela."""
        try:
            return self.aeroportos[icao]
        except KeyError:
            raise ValueError(f"aeroporto {icao} sem tradução na tabela") from None

    def codigo_vendido(self, empresa: str) -> str:
        """O código do bilhete (AZU -> AD, TAM -> LA); sem tradução, o ICAO."""
        return (self.companhias.get(empresa) or {}).get("iata") or empresa

    def iata(self, aeroporto: str) -> str:
        """O IATA do aeroporto (SBSP -> CGH); sem tradução, o ICAO."""
        return (self.aeroportos.get(aeroporto) or {}).get("iata") or aeroporto

    def rotulo(self, chave: tuple[str, ...], por: str = "voo") -> str:
        """A chave de `agrupar` como o passageiro lê: 'G3 1044 CGH→SDU'."""
        if por == "voo":
            empresa, numero, origem, destino = chave
            return f"{self.codigo_vendido(empresa)} {numero} {self.iata(origem)}→{self.iata(destino)}"
        if por == "rota":
            return f"{self.iata(chave[0])}→{self.iata(chave[1])}"
        if por == "companhia":
            nome = (self.companhias.get(chave[0]) or {}).get("nome_exibicao")
            return f"{nome} ({chave[0]})" if nome else chave[0]
        nome = (self.aeroportos.get(chave[0]) or {}).get("nome_exibicao")
        return f"{self.iata(chave[0])} {nome}" if nome else chave[0]


def _ler(nome: str) -> dict:
    texto = files("vra_anac").joinpath("dados", nome).read_text(encoding="utf-8")
    return {linha["icao"]: linha for linha in csv.DictReader(io.StringIO(texto, newline=""))}


@lru_cache(maxsize=1)
def tabelas() -> Tabelas:
    """As tabelas que vêm com o pacote (lidas uma vez)."""
    return Tabelas(_ler("companhias.csv"), _ler("aeroportos.csv"))
