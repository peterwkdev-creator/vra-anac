"""A leitura do CSV do VRA. A fixture tem linhas REAIS do arquivo de
julho/2026 da ANAC (dado aberto, CC-BY), uma de cada caso, com os bytes do
arquivo original: BOM e CRLF."""
from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path

import vra_anac
from vra_anac import leitura

FIXTURE = Path(__file__).parent / "fixtures" / "vra-amostra.csv"
AMOSTRA = FIXTURE.read_text(encoding="utf-8-sig")


def _ops():
    _, linhas = leitura.ler(AMOSTRA)
    return leitura.regulares_domesticas(linhas)


def _minutos(segundos):
    return None if segundos is None else segundos / 60


class Leitura(unittest.TestCase):
    def test_metadado_e_cabecalho_do_arquivo_real(self):
        atualizado, linhas = leitura.ler(AMOSTRA)
        self.assertEqual(atualizado, "2026-08-28")
        self.assertEqual(len(linhas), 7)

    def test_recusa_arquivo_sem_as_colunas_esperadas(self):
        quebrado = AMOSTRA.replace("Partida Real", "Partida Efetiva")
        with self.assertRaises(ValueError):
            leitura.ler(quebrado)

    def test_recusa_primeira_linha_que_nao_e_metadado(self):
        with self.assertRaises(ValueError):
            leitura.ler(AMOSTRA.split("\n", 1)[1])

    def test_so_domestico_regular(self):
        # das 7 linhas, saem o voo não regular (autorização 4, previsto null)
        # e o internacional (tipo I); ficam 5, incluindo o de agosto
        ops = _ops()
        self.assertEqual(len(ops), 5)
        self.assertTrue(all(o.empresa in {"GLO", "AZU"} for o in ops))

    def test_null_textual_e_cancelado(self):
        cancelado = [o for o in _ops() if o.cancelado]
        self.assertEqual(len(cancelado), 1)
        self.assertIsNone(cancelado[0].partida_real)
        self.assertIsNone(cancelado[0].atraso_partida_s)
        self.assertIsNone(cancelado[0].atraso_chegada_s)

    def test_fracao_de_segundo_no_previsto(self):
        # medido: 6.834 previstos com ".100000000" em julho/2026
        azu = next(o for o in _ops() if o.empresa == "AZU")
        self.assertEqual(azu.partida_prevista, datetime(2026, 7, 17, 16, 55))
        self.assertEqual(_minutos(azu.atraso_partida_s), 88)
        self.assertEqual(_minutos(azu.atraso_chegada_s), 85)

    def test_atraso_e_antecipacao(self):
        por_data = {o.partida_prevista.date().isoformat(): o for o in _ops()}
        self.assertEqual(_minutos(por_data["2026-07-18"].atraso_partida_s), -6)
        self.assertEqual(_minutos(por_data["2026-07-18"].atraso_chegada_s), -15)
        self.assertEqual(_minutos(por_data["2026-07-23"].atraso_partida_s), 64)
        self.assertEqual(_minutos(por_data["2026-07-23"].atraso_chegada_s), 56)

    def test_periodo_sai_das_datas(self):
        mes, fora = leitura.periodo(_ops())
        self.assertEqual((mes, fora), ("2026-07", 1))

    def test_periodo_sem_operacao(self):
        with self.assertRaises(ValueError):
            leitura.periodo([])

    def test_situacao_desconhecida_para_a_leitura(self):
        _, linhas = leitura.ler(AMOSTRA.replace('"CANCELADO"', '"ADIADO"'))
        with self.assertRaisesRegex(ValueError, "linha 6: situação desconhecida"):
            leitura.regulares_domesticas(linhas)

    def test_ler_arquivo_com_bom_e_crlf(self):
        self.assertTrue(FIXTURE.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"\r\n", FIXTURE.read_bytes())
        atualizado, ops = vra_anac.ler_arquivo(FIXTURE)
        self.assertEqual(atualizado, "2026-08-28")
        self.assertEqual(len(ops), 5)


class NumeroVendido(unittest.TestCase):
    def test_tira_o_z_so_antes_de_digitos(self):
        self.assertEqual(leitura.numero_vendido("Z1001"), "1001")
        self.assertEqual(leitura.numero_vendido("1001"), "1001")
        self.assertEqual(leitura.numero_vendido("ZA01"), "ZA01")
        self.assertEqual(leitura.numero_vendido("Z"), "Z")

    def test_chave_usa_o_numero_vendido(self):
        op = _ops()[0]
        com_z = leitura.Operacao(op.empresa, "Z" + op.numero, op.origem, op.destino,
                                 op.partida_prevista, op.partida_real, op.chegada_prevista,
                                 op.chegada_real, op.cancelado)
        self.assertEqual(com_z.chave, op.chave)
        self.assertEqual(op.chave, ("GLO", "1015", "SBRJ", "SBSP"))


if __name__ == "__main__":
    unittest.main()
