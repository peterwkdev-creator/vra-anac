"""Pontualidade dos voos domésticos do Brasil, pelo arquivo mensal do VRA da ANAC.

Lê o CSV como a ANAC publica (BOM, metadado na 1ª linha, `null` no lugar
de vazio), fica com os voos domésticos regulares e conta quantos chegaram
no horário: até 15 min depois da prevista, a régua do chegounahora.com.br.

    import vra_anac
    atualizado, voos = vra_anac.ler_arquivo("VRA_20267.csv")
    por_voo = vra_anac.agrupar(voos, por="voo", minimo=20)

Dados: ANAC, Voo Regular Ativo (VRA), licença CC-BY.
"""
from vra_anac.indicador import (AGRUPAMENTOS, LIMITES_MIN, NO_HORARIO_MIN, Contagem, Fatia,
                                agrupar, chave, porcento)
from vra_anac.leitura import (Operacao, ler, ler_arquivo, numero_vendido, periodo,
                              regulares_domesticas)
from vra_anac.tabelas import Tabelas, tabelas

__version__ = "0.1.0"

__all__ = [
    "AGRUPAMENTOS", "LIMITES_MIN", "NO_HORARIO_MIN",
    "Contagem", "Fatia", "Operacao", "Tabelas",
    "agrupar", "chave", "ler", "ler_arquivo", "numero_vendido", "periodo", "porcento",
    "regulares_domesticas", "tabelas",
]
