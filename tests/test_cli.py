"""A linha de comando: saída em texto e JSON, erros e ajuda em português."""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

from vra_anac.__main__ import ATRIBUICAO, _milhar, main

FIXTURE = str(Path(__file__).parent / "fixtures" / "vra-amostra.csv")
INGLES = re.compile(r"\b(usage|options|positional|arguments?|required|invalid|"
                    r"error|show this help|expected)\b", re.I)


def _rodar(*args):
    saida, erro = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(erro):
        try:
            codigo = main(list(args))
        except SystemExit as e:
            codigo = e.code
    return codigo, saida.getvalue(), erro.getvalue()


class Saida(unittest.TestCase):
    def test_texto_por_voo(self):
        codigo, saida, _ = _rodar(FIXTURE, "--minimo", "1")
        self.assertEqual(codigo, 0)
        self.assertIn("07/2026 (arquivo atualizado em 2026-08-28): 5 voos domésticos "
                      "regulares, 1 fora do mês.", saida)
        self.assertIn("Só os grupos com 1 voo ou mais.", saida)
        linhas = [l.split() for l in saida.splitlines() if "%" in l]
        # o de 100% primeiro; depois, no empate em 0%, o de mais voos
        self.assertEqual(linhas[0], ["100%", "0%", "1", "G3", "1015", "SDU→CGH"])
        self.assertEqual(linhas[1], ["0%", "50%", "2", "G3", "1016", "CGH→SDU"])
        self.assertTrue(saida.rstrip().endswith(ATRIBUICAO))

    def test_milhar_com_ponto(self):
        self.assertEqual([_milhar(n) for n in (5, 999, 1098, 68355, 1234567)],
                         ["5", "999", "1.098", "68.355", "1.234.567"])

    def test_minimo_padrao_20_deixa_a_fixture_vazia(self):
        codigo, saida, _ = _rodar(FIXTURE)
        self.assertEqual(codigo, 0)
        self.assertIn("Nenhum grupo com 20 voos ou mais.", saida)

    def test_json(self):
        codigo, saida, _ = _rodar(FIXTURE, "--por", "companhia", "--minimo", "1", "--json")
        self.assertEqual(codigo, 0)
        d = json.loads(saida)
        self.assertEqual((d["mes"], d["voos"], d["fora_do_mes"]), ("2026-07", 5, 1))
        self.assertIn("ANAC", d["atribuicao"])
        glo = d["grupos"][0]
        self.assertEqual((glo["rotulo"], glo["voos"], glo["chegada_no_horario_pct"],
                          glo["cancelado_pct"]), ("GOL (GLO)", 4, 25, 25))
        self.assertEqual(glo["chegada"], {"no_horario": 25, "ate30": 0, "ate60": 50,
                                          "acima60": 0, "cancelado": 25})


class Erros(unittest.TestCase):
    def test_arquivo_ausente(self):
        codigo, _, erro = _rodar("nao-existe.csv")
        self.assertEqual(codigo, 1)
        self.assertIn("erro: arquivo não encontrado: nao-existe.csv", erro)

    def test_pasta(self):
        codigo, _, erro = _rodar(str(Path(__file__).parent))
        self.assertEqual(codigo, 1)
        self.assertIn("é uma pasta", erro)

    def test_arquivo_que_nao_e_o_vra(self):
        codigo, _, erro = _rodar(__file__)
        self.assertEqual(codigo, 1)
        self.assertIn("1ª linha não é o metadado esperado", erro)

    def test_erros_do_argparse_em_portugues(self):
        for args in ([], [FIXTURE, "--minimo", "0"], [FIXTURE, "--por", "estado"],
                     [FIXTURE, "--xyz"]):
            with self.subTest(args=args):
                codigo, _, erro = _rodar(*args)
                self.assertEqual(codigo, 2)
                self.assertIn("uso:", erro)
                self.assertIsNone(INGLES.search(erro), erro)


class Ajuda(unittest.TestCase):
    def test_ajuda_em_portugues_com_atribuicao(self):
        codigo, saida, _ = _rodar("--help")
        self.assertEqual(codigo, 0)
        self.assertTrue(saida.startswith("uso: "))
        self.assertIsNone(INGLES.search(saida), saida)
        self.assertIn("ANAC", saida)

    def test_nome_do_comando_instalado(self):
        with mock.patch.object(sys, "argv", ["/venv/bin/vra-anac"]):
            _, saida, _ = _rodar("--help")
        self.assertTrue(saida.startswith("uso: vra-anac "))
        with mock.patch.object(sys, "argv", ["/x/vra_anac/__main__.py"]):
            _, saida, _ = _rodar("--help")
        self.assertTrue(saida.startswith("uso: python -m vra_anac "))


if __name__ == "__main__":
    unittest.main()
