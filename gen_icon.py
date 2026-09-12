# -*- coding: utf-8 -*-
"""Gera assets/app.ico (ícone pastel do Tarefas Diárias). Pode regenerar: python gen_icon.py"""

import os
from PIL import Image, ImageDraw

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)

TAM = 256
img = Image.new("RGBA", (TAM, TAM), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
r = 64  # raio do canto

# fundo: quadrado arredondado pêssego
d.rounded_rectangle([8, 8, TAM - 8, TAM - 8], radius=r, fill="#FFB3A7")

# folhinha de tarefa branca
folha = [56, 56, TAM - 56, TAM - 56]
d.rounded_rectangle(folha, radius=24, fill="#FFFDFC")

# linhas de tarefa
cx = 96
d.line([cx, 110, TAM - cx, 110], fill="#EADCD5", width=8)
d.line([cx, 150, TAM - cx - 20, 150], fill="#EADCD5", width=8)

# checkbox azul (primeira tarefa "feita")
d.rounded_rectangle([cx, 96, cx + 44, 140], radius=10, fill="#CBE6F7")
d.line([cx + 10, 118, cx + 20, 130], fill="#3E8FA0", width=7)
d.line([cx + 20, 130, cx + 36, 106], fill="#3E8FA0", width=7)

# bolinha da segunda tarefa
d.ellipse([cx, 136, cx + 44, 180], fill="#FFD9B8")
d.ellipse([cx + 14, 150, cx + 30, 166], fill="#FFB3A7")

# coraçãozinho no canto
def coracao(dd, cx0, cy0, s, cor):
    dd.ellipse([cx0 - s, cy0 - s, cx0, cy0], fill=cor)
    dd.ellipse([cx0, cy0 - s, cx0 + s, cy0], fill=cor)
    dd.polygon([(cx0 - s - s // 4, cy0 - s // 3), (cx0 + s + s // 4, cy0 - s // 3), (cx0, cy0 + s)], fill=cor)

coracao(d, TAM - 84, 100, 30, "#FFC9D6")

sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
img.save(os.path.join(ASSETS, "app.ico"), sizes=sizes)
img.save(os.path.join(ASSETS, "app.png"))
print("OK ->", os.path.join(ASSETS, "app.ico"))