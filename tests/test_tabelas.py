"""As tabelas que vêm com o pacote: do ICAO ao código do bilhete."""
from __future__ import annotations

import unittest

import vra_anac


class Tabelas(unittest.TestCase):
    def setUp(self):
        self.t = vra_anac.tabelas()

    def test_codigo_vendido(self):
        self.assertEqual(self.t.codigo_vendido("GLO"), "G3")
        self.assertEqual(self.t.codigo_vendido("TAM"), "LA")  # cadastro JJ, vende LA
        self.assertEqual(self.t.codigo_vendido("ACN"), "AD")  # Azul Conecta vende como Azul
        self.assertEqual(self.t.codigo_vendido("XYZ"), "XYZ")

    def test_rotulos(self):
        self.assertEqual(self.t.rotulo(("GLO", "1044", "SBSP", "SBRJ")), "G3 1044 CGH→SDU")
        self.assertEqual(self.t.rotulo(("SBSP", "SBRJ"), "rota"), "CGH→SDU")
        self.assertEqual(self.t.rotulo(("AZU",), "companhia"), "Azul (AZU)")
        self.assertEqual(self.t.rotulo(("XYZ",), "companhia"), "XYZ")
        self.assertEqual(self.t.rotulo(("SBSP",), "origem"), "CGH Congonhas")
        self.assertEqual(self.t.rotulo(("SXXX",), "destino"), "SXXX")

    def test_codigo_ausente_na_consulta_direta(self):
        with self.assertRaises(ValueError):
            self.t.companhia("XYZ")
        with self.assertRaises(ValueError):
            self.t.aeroporto("SXXX")

    def test_toda_linha_tem_fonte(self):
        for nome, tabela, coluna in (("companhias", self.t.companhias, "fonte_url"),
                                     ("aeroportos", self.t.aeroportos, "fonte_nome")):
            with self.subTest(tabela=nome):
                self.assertGreater(len(tabela), 0)
                self.assertEqual([k for k, l in tabela.items() if not l[coluna]], [])


if __name__ == "__main__":
    unittest.main()
