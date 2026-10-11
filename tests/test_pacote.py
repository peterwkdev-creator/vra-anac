"""O pacote instalado: todo arquivo não-.py que ele lê vai junto (o package-data), o --version é o __version__
e o pyproject cabe no About e nos tópicos do GitHub."""

import importlib
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PACOTE = "vra_anac"


@unittest.skipIf(sys.version_info < (3, 11), "tomllib entra no 3.11; o CI roda também nas novas")
class TestEmpacotamento(unittest.TestCase):

    def test_dados_do_pacote_no_package_data(self):
        # um .tsv passava no checkout e sumia no pip install, sem aviso
        import tomllib
        cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
        dados = cfg.get("tool", {}).get("setuptools", {}).get("package-data", {})
        padroes = dados.get(PACOTE, []) + dados.get("*", [])
        pasta = RAIZ / PACOTE
        # glob do Path, como o setuptools: o fnmatch deixava "*.tsv" valer em subpasta
        cobertos = {p for g in padroes for p in pasta.glob(g)}
        fora = [p.relative_to(pasta).as_posix() for p in sorted(pasta.rglob("*"))
                if p.is_file() and p.suffix not in (".py", ".pyc") and "__pycache__" not in p.parts
                and p not in cobertos]
        self.assertEqual(fora, [], "fora do [tool.setuptools.package-data]: não vão na instalação")

    def test_subpacotes_no_packages(self):
        # packages = ["vra_anac"] não leva subpasta com .py: o import quebra só depois do pip install
        import tomllib
        cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
        pacotes = cfg.get("tool", {}).get("setuptools", {}).get("packages", [])
        if not isinstance(pacotes, list):
            return  # packages.find acha os subpacotes sozinho
        pasta = RAIZ / PACOTE
        subs = sorted({".".join((PACOTE,) + p.parent.relative_to(pasta).parts)
                       for p in pasta.rglob("*.py") if "__pycache__" not in p.parts})
        self.assertEqual([s for s in subs if s not in pacotes], [],
                         "fora do packages do [tool.setuptools]: não vão na instalação")

    def test_about_e_topicos_que_o_github_aceita(self):
        # o description e as keywords viram o About e os tópicos (gh repo edit): o GitHub
        # aceita até 20 tópicos, cada um com minúsculas, dígitos e hífen, e About até 350
        import tomllib
        cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        topicos = cfg.get("keywords", [])
        self.assertLessEqual(len(topicos), 20, "o GitHub aceita até 20 tópicos")
        self.assertEqual(len(set(topicos)), len(topicos), "tópico repetido")
        for t in topicos:
            self.assertRegex(t, r"^[a-z0-9][a-z0-9-]{0,49}$", "tópico do GitHub: minúsculas, dígitos e hífen")
        self.assertLessEqual(len(cfg.get("description", "")), 350, "About do GitHub: até 350 caracteres")
        for nome, url in cfg.get("urls", {}).items():
            self.assertTrue(url.startswith("https://"), f"{nome}: o PyPI e o GitHub pedem https")


class TestVersao(unittest.TestCase):

    def test_version_da_cli_e_o_do_pacote(self):
        # a versão vem do pacote: um "1.0.0" escrito à mão quebra na 1.1.0
        versao = importlib.import_module(PACOTE).__version__
        r = subprocess.run([sys.executable, "-m", PACOTE, "--version"], cwd=RAIZ,
                           capture_output=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(versao, r.stdout.split())


if __name__ == "__main__":
    unittest.main()
