"""O indicador: no horário até 15 min pela chegada, faixas 30 e 60,
cancelado sobre o total. Cada número esperado foi contado à mão."""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from pathlib import Path

import vra_anac
from vra_anac import indicador
from vra_anac.leitura import Operacao

FIXTURE = Path(__file__).parent / "fixtures" / "vra-amostra.csv"


def _op(chegada_min=0, partida_min=0, cancelado=False, numero="1000",
        empresa="GLO", origem="SBSP", destino="SBRJ"):
    """Voo inventado: atrasos em minutos sobre o previsto."""
    pp = datetime(2026, 7, 1, 10, 0)
    cp = pp + timedelta(hours=1)
    pr = None if cancelado else pp + timedelta(minutes=partida_min)
    cr = None if cancelado else cp + timedelta(minutes=chegada_min)
    return Operacao(empresa, numero, origem, destino, pp, pr, cp, cr, cancelado)


class Porcento(unittest.TestCase):
    def test_meio_para_cima(self):
        self.assertEqual(indicador.porcento(1, 8), 13)   # 12,5
        self.assertEqual(indicador.porcento(1, 200), 1)  # 0,5; round() daria 0
        self.assertEqual(indicador.porcento(0, 3), 0)

    def test_sobre_zero(self):
        with self.assertRaises(ValueError):
            indicador.porcento(0, 0)


class Limites(unittest.TestCase):
    def test_15_min_exatos_e_no_horario_15_e_1_s_nao(self):
        c = vra_anac.Contagem()
        c.somar(_op(chegada_min=15))
        op = _op()
        c.somar(Operacao(op.empresa, op.numero, op.origem, op.destino, op.partida_prevista,
                         op.partida_real, op.chegada_prevista,
                         op.chegada_prevista + timedelta(minutes=15, seconds=1), False))
        self.assertEqual(c.chegada_no_horario, 1)

    def test_30_e_60_exatos_nao_passam_da_faixa(self):
        c = vra_anac.Contagem()
        for m in (30, 31, 60, 61):
            c.somar(_op(chegada_min=m))
        self.assertEqual(c.chegada_acima, {30: 3, 60: 1})

    def test_adiantado_conta_no_horario(self):
        c = vra_anac.Contagem()
        c.somar(_op(chegada_min=-20, partida_min=-5))
        self.assertEqual((c.chegada_no_horario, c.partida_no_horario), (1, 1))

    def test_realizado_sem_horario_real_para(self):
        op = _op()
        sem = Operacao(op.empresa, op.numero, op.origem, op.destino, op.partida_prevista,
                       op.partida_real, op.chegada_prevista, None, False)
        with self.assertRaisesRegex(ValueError, "sem horário real"):
            vra_anac.Contagem().somar(sem)


class Contagem(unittest.TestCase):
    def setUp(self):
        self.c = vra_anac.Contagem()
        # 8 voos: 4 no horário, 1 com 20 min, 1 com 45, 1 com 90, 1 cancelado
        for m in (0, 5, -3, 15, 20, 45, 90):
            self.c.somar(_op(chegada_min=m, partida_min=m + 10))
        self.c.somar(_op(cancelado=True))

    def test_percentuais(self):
        self.assertEqual(self.c.n, 8)
        self.assertEqual(self.c.pct("chegada"), 50)
        self.assertEqual(self.c.pct("cancelado"), 13)   # 12,5
        self.assertEqual(self.c.pct("chegada>30"), 25)  # 45 e 90
        self.assertEqual(self.c.pct("chegada>60"), 13)  # 90
        # partida = chegada + 10: no horário 0, 5 e -3 (o 15 vira 25)
        self.assertEqual(self.c.pct("partida"), 38)    # 3/8 = 37,5

    def test_distribuicao_soma_o_n(self):
        fatias = self.c.distribuicao("chegada")
        self.assertEqual([(f.chave, f.voos) for f in fatias],
                         [("no_horario", 4), ("ate30", 1), ("ate60", 1),
                          ("acima60", 1), ("cancelado", 1)])
        self.assertEqual(sum(f.voos for f in fatias), self.c.n)
        self.assertEqual(fatias[1].largura, "12.500")


class Agrupar(unittest.TestCase):
    def setUp(self):
        _, self.ops = vra_anac.ler_arquivo(FIXTURE)

    def test_por_voo_na_fixture(self):
        g = vra_anac.agrupar(self.ops, "voo")
        self.assertEqual(len(g), 4)
        c = g[("GLO", "1016", "SBSP", "SBRJ")]
        # 23/07 chegou 56 min depois; 15/07 cancelado
        self.assertEqual((c.n, c.pct("chegada"), c.pct("cancelado"), c.pct("chegada>30")),
                         (2, 0, 50, 50))
        self.assertEqual(g[("GLO", "1015", "SBRJ", "SBSP")].pct("chegada"), 100)

    def test_por_companhia_rota_origem_destino(self):
        self.assertEqual({k: c.n for k, c in vra_anac.agrupar(self.ops, "companhia").items()},
                         {("GLO",): 4, ("AZU",): 1})
        self.assertEqual(vra_anac.agrupar(self.ops, "companhia")[("GLO",)].pct("chegada"), 25)
        self.assertEqual(vra_anac.agrupar(self.ops, "rota")[("SBSP", "SBRJ")].n, 2)
        self.assertEqual(vra_anac.agrupar(self.ops, "origem")[("SBSP",)].n, 2)
        self.assertEqual(vra_anac.agrupar(self.ops, "destino")[("SBRJ",)].n, 2)

    def test_minimo(self):
        self.assertEqual(list(vra_anac.agrupar(self.ops, "voo", minimo=2)),
                         [("GLO", "1016", "SBSP", "SBRJ")])

    def test_numero_com_z_soma_no_mesmo_voo(self):
        g = vra_anac.agrupar([_op(numero="1000"), _op(numero="Z1000")], "voo")
        self.assertEqual({k: c.n for k, c in g.items()}, {("GLO", "1000", "SBSP", "SBRJ"): 2})

    def test_agrupamento_desconhecido(self):
        with self.assertRaisesRegex(ValueError, "agrupamento desconhecido"):
            vra_anac.agrupar(self.ops, "estado")


if __name__ == "__main__":
    unittest.main()
