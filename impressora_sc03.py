# -*- coding: utf-8 -*-
"""
impressora_sc03.py — Versão Python do print.md (SC03h-12BC).
Roda SEM IA. Usa o wrapper oficial print-sc03.ps1 (linha de corte + feed + bip
+ contador de rolo automaticamente). Também pode chamar o timiniprint.exe direto.

Uso:
    import impressora_sc03
    ok, msg = impressora_sc03.imprimir_texto("OLÁ MUNDO", preset="forte")
"""

import os
import subprocess
import sys

PASTA_TOOLS = os.path.join(os.path.expanduser("~"), "Desktop", ".opencode", "tools", "timiniprint")
TOOL = os.path.join(PASTA_TOOLS, "timiniprint.exe")
WRAPPER = os.path.join(PASTA_TOOLS, "print-sc03.ps1")

PRESETS = {
    "fraco": {"desc": "leve, preserva a cabeça", "darkness": 2},
    "medio": {"desc": "padrão do aparelho", "darkness": 3},
    "forte": {"desc": "escuro e nítido", "darkness": 5},
    "max": {"desc": "MÁXIMO SEGURO", "darkness": 5},
}

COLUNAS_VALIDAS = ("10", "16", "32")


def disponivel():
    """True se a ferramenta da impressora existe neste PC."""
    return os.path.exists(TOOL) and os.path.exists(WRAPPER)


def caminhos():
    return TOOL, WRAPPER


def imprimir_texto(texto, preset="forte", colunas=16, silencioso=True):
    """Imprime texto na SC03 via wrapper (corte + feed + bip).

    Retorna (ok: bool, mensagem: str).
    """
    if not disponivel():
        return False, "Impressora SC03 não encontrada neste PC (falta .opencode/tools/timiniprint)."
    if preset not in PRESETS:
        preset = "forte"
    if str(colunas) not in COLUNAS_VALIDAS:
        colunas = 16
    cfg = os.path.join(PASTA_TOOLS, "sc03-%s.json" % preset)

    args = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", WRAPPER,
        "-Text", texto, "-Preset", preset, "-Columns", str(colunas),
    ]
    try:
        res = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except Exception as e:
        return False, "Erro ao executar impressão: %s" % e

    saida = (res.stdout or "").strip()
    if res.returncode == 0:
        return True, saida or "Impresso com sucesso."
    return False, (res.stderr or saida or "Falha ao imprimir (código %s)." % res.returncode)


def montar_linhas(tarefas, quais="pendentes", por_categoria=False):
    """Monta as linhas das tarefas para impressão.

    quais: "pendentes" | "concluidas" | "todas"
    por_categoria: True agrupa com um cabeçalho por categoria
    (por padrão NÃO imprime categoria — só o que pede o usuário).

    Retorna lista de strings prontas para impressão.
    """
    PR = {"alta": 0, "media": 1, "baixa": 2}
    itens = [t for t in tarefas if not t.get("concluida")] if quais == "pendentes" else (
        [t for t in tarefas if t.get("concluida")] if quais == "concluidas" else list(tarefas))
    if not itens:
        return []

    itens.sort(key=lambda t: (
        1 if t.get("concluida") else 0,
        (t.get("categoria") or "").strip().upper() or "zzz",
        t.get("data") or "9999-99-99",
        PR.get((t.get("prioridade") or "media").lower(), 1),
    ))

    linhas = ["=== TAREFAS DIARIAS ==="]
    marcar = {True: "[x]", False: "[ ]"}
    cat_atual = None
    for t in itens:
        cat = (t.get("categoria") or "").strip()
        if por_categoria and cat and cat.upper() != cat_atual:
            cat_atual = cat.upper()
            linhas.append("--- %s ---" % cat)
        prio = (t.get("prioridade") or "media").title()
        linhas.append("%s %s  [%s]" % (
            marcar.get(bool(t.get("concluida"))),
            t.get("titulo", "?"),
            prio,
        ))
    return linhas


def montar_linhas_pendentes(tarefas):
    """Linhas das tarefas pendentes (mantido para compatibilidade)."""
    return montar_linhas(tarefas, quais="pendentes")


def imprimir_tarefas(tarefas, quais="pendentes", por_categoria=False, preset="forte", colunas=16):
    """Monta o texto das tarefas (pendentes/concluídas/todas) e imprime."""
    linhas = montar_linhas(tarefas, quais=quais, por_categoria=por_categoria)
    if not linhas:
        return True, "Nenhuma tarefa pra imprimir."
    texto = "\n".join(linhas)
    return imprimir_texto(texto, preset=preset, colunas=colunas)


def imprimir_pendentes(tarefas, preset="forte", colunas=16):
    """Imprime as tarefas pendentes (mantido para compatibilidade)."""
    return imprimir_tarefas(tarefas, quais="pendentes", preset=preset, colunas=colunas)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print("disponivel:", disponivel())
        print("tool:", TOOL)
        print("wrapper:", WRAPPER)
    else:
        ok, msg = imprimir_texto("TESTE SC03", preset="forte")
        print("OK" if ok else "ERRO", "->", msg)