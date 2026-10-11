"""Grava docs/vitrine.gif: o vra-anac rodando num terminal, com a saída real.

    python docs/gravar-gif.py . VRA_20268.csv

Ferramenta de quem mantém, fora do pacote: precisa do Pillow e da fonte
Consolas (Windows). Regravar quando a saída da linha de comando mudar.
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

raiz, csv = Path(sys.argv[1]), Path(sys.argv[2])
FONTE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 15)
FONTE_N = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 15)
LARG, ALT, MARGEM, LINHA = 880, 400, 18, 21
FUNDO, TEXTO, PROMPT, CMD, BARRA = "#1e1e1e", "#d4d4d4", "#6a9955", "#ffffff", "#333333"

COMANDOS = [["--por", "companhia"], ["--por", "rota", "--minimo", "200"]]


def saida(args):
    r = subprocess.run([sys.executable, "-m", "vra_anac", str(csv), *args], cwd=raiz,
                       capture_output=True, encoding="utf-8", check=True)
    linhas = r.stdout.splitlines()
    # a atribuição sai inteira no terminal; no GIF, sem a URL, para caber
    linhas = [l.split(" https://")[0] for l in linhas]
    return linhas


def quadro(texto_linhas):
    im = Image.new("RGB", (LARG, ALT), FUNDO)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, LARG, 26], fill=BARRA)
    for i, cor in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        d.ellipse([12 + i * 20, 8, 24 + i * 20, 20], fill=cor)
    y = 26 + 10
    for tipo, t in texto_linhas[-((ALT - 40) // LINHA):]:
        if tipo == "cmd":
            d.text((MARGEM, y), "$ ", font=FONTE_N, fill=PROMPT)
            d.text((MARGEM + FONTE.getlength("$ "), y), t, font=FONTE_N, fill=CMD)
        else:
            d.text((MARGEM, y), t, font=FONTE, fill=TEXTO)
        y += LINHA
    return im


quadros, tempos = [], []
tela = []
for args in COMANDOS:
    cmd = " ".join(["vra-anac", csv.name, *args])
    tela = []
    for k in range(0, len(cmd) + 1, 2):
        quadros.append(quadro(tela + [("cmd", cmd[:k] + "▌")]))
        tempos.append(55)
    tela = tela + [("cmd", cmd)]
    quadros.append(quadro(tela)); tempos.append(500)
    linhas = saida(args)
    if "rota" in args:
        linhas = linhas[:4] + linhas[4:12] + ["       ...", ""] + [linhas[-1]]
    tela = tela + [("out", l) for l in linhas]
    quadros.append(quadro(tela)); tempos.append(4500)

destino = raiz / "docs" / "vitrine.gif"
destino.parent.mkdir(exist_ok=True)
# uma paleta para todos os quadros, com as cores fixas garantidas
base = quadros[-1].copy()
for i, cor in enumerate(("#ff5f56", "#ffbd2e", "#27c93f", PROMPT, CMD, TEXTO)):
    ImageDraw.Draw(base).rectangle([i * 140, ALT - 60, i * 140 + 139, ALT], fill=cor)
ref = base.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
pal = [q.quantize(palette=ref, dither=Image.Dither.NONE) for q in quadros]
pal[0].save(destino, save_all=True, append_images=pal[1:], duration=tempos, loop=0,
            optimize=True)
print(destino, destino.stat().st_size, "bytes,", len(quadros), "quadros,",
      sum(tempos) / 1000, "s")
