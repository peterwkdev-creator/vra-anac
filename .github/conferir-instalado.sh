#!/usr/bin/env bash
# Monta o sdist e o wheel em dist/ e roda o que o pip instala, num venv e
# fora do checkout (de dentro dele, o import pegaria a cópia local). Roda no
# testes.yml a cada push (job "pacote") e no pypi.yml antes de publicar.
set -euo pipefail
# fora do CI (prova local, roteiro passo 2) não há RUNNER_TEMP
tmp="${RUNNER_TEMP:-$(mktemp -d)}"
python -m pip install --quiet "build==1.6.1"
# egg-info de um build anterior leva ao wheel o que o package-data não lista
# (e o controle passaria por engano); no CI o checkout já é limpo
rm -rf build dist ./*.egg-info src/*.egg-info
python -m build
venv="$tmp/instalado"
python -m venv "$venv"
"$venv/bin/pip" install --quiet dist/*.whl
# a amostra do VRA fica no checkout; o comando roda de fora dele
amostra="$PWD/tests/fixtures/vra-amostra.csv"
cd "$tmp"
# a versão que o pip instalou é a do __version__ (a CLI responde --version)
v=$("$venv/bin/python" -I -c 'import vra_anac as p; print(p.__version__)')
"$venv/bin/python" -I -m vra_anac --version | grep -F "$v"
# Um valor do README, pelo que o pip instalou: o comando no PATH, com a
# ajuda em português, e o rótulo que só sai se as tabelas (package-data)
# foram no wheel.
"$venv/bin/vra-anac" --help | grep -F "uso: vra-anac "
"$venv/bin/vra-anac" "$amostra" --minimo 1 | grep -F "G3 1016 CGH→SDU"
