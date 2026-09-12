# -*- coding: utf-8 -*-
"""
tarefas.py — Tarefas Diárias ✿ (estética Pastel XP kawaii, inspirada no PC Sara)

App de criação e gerenciamento de tarefas diárias. Roda SEM IA.
- Salva em JSON (autosave) em tarefas.json ao lado do programa
- Exporta / importa JSON
- Imprime as pendentes na impressora térmica SC03 (se presente)
- Visual pastel estilo "Mini PC XP" do Desktop\\pc sara

Rodar:  python tarefas.py
Rodar:  python tarefas.py --selftest   (abre e fecha sozinho, para teste)
"""

import ctypes
import datetime
import json
import os
import sys

import impressora_sc03
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

APPDIR = os.path.dirname(
    os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)
)
ARQ_PADRAO = os.path.join(APPDIR, "tarefas.json")
ASSETS = os.path.join(APPDIR, "assets")
ICONE = os.path.join(ASSETS, "app.ico")

# ---------------------------------------------------------------------------
# Versão do app (exibida no HUD)
# ---------------------------------------------------------------------------
VERSAO = "1.1.0"
VERSAO_DATA = "2026-09-12"
VERSAO_LABEL = "v%s · %s" % (VERSAO, VERSAO_DATA)

# ---------------------------------------------------------------------------
# Paleta Pastel XP kawaii (inspirada na estetica.txt do PC Sara)
# ---------------------------------------------------------------------------
BG = "#FDF6F2"          # rosa clarinho (fundo)
PANEL = "#FFFDFC"       # branco quente
PANEL_ALT = "#FFF3EE"   # rosa clarinho (linhas alternadas)
TITLEBAR = "#FFC9D6"    # rosa (barra de título)
TITLEBAR_TEXT = "#6E4A54"
STRIPE = ["#FFC9D6", "#FFD9B8", "#FBE2BE", "#CBE6F7"]  # bandeirinha pastel XP
PRIMARY = "#FFB3A7"     # pêssego (botão principal)
PRIMARY_HOVER = "#FF9E90"
ACCENT = "#CBE6F7"      # azul clarinho (botões secundários)
ACCENT_HOVER = "#AED9F0"
TEXT = "#5A4641"
TEXT_SOFT = "#9C8B85"
LINE = "#EADCD5"
DANGER = "#E88A98"

HIGH = "#C9506B"        # prioridade alta
MED = "#C97A3E"         # prioridade média
LOW = "#3E8FA0"         # prioridade baixa
DONE = "#B7ABA5"        # tarefa concluída

FONTE = "Segoe UI"
FONTE_SERIF = "Segoe UI"

# Impressora SC03: papel térmico 58 mm, área de impressão 384 px = 48 mm (margem lateral 5 mm)
PAPEL_W_MM = 58.0
PRINT_W_MM = 48.0
PRINT_W_PX = 384
TXT_PLACEHOLDER = "Escreva aqui o texto livre…"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def hoje_iso():
    return datetime.date.today().isoformat()


def data_exibir(iso):
    if not iso:
        return "—"
    try:
        return datetime.datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


def dias_ate(iso):
    try:
        d = datetime.datetime.strptime(iso, "%Y-%m-%d").date()
        return (d - datetime.date.today()).days
    except Exception:
        return None

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class TarefasApp:
    def __init__(self, root):
        self.root = root
        self.ppi = float(self.root.winfo_fpixels("1i") or 96.0)
        self.categorias_padrao = ["Pessoal", "Empresa", "Estudos", "Jogos", "Outros"]
        self.tarefas = []
        self.filtro = "Todas"
        self.busca = ""
        self._carregar()

        self._build_style()
        self._build_ui()
        self._bind()
        self.atualizar()

    # ---------- estilo ttk ----------
    def _build_style(self):
        s = ttk.Style(self.root)
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TFrame", background=BG)
        s.configure("Panel.TFrame", background=PANEL)
        s.configure(
            "TButton",
            font=(FONTE, 9),
            padding=(12, 5),
            relief="flat",
            background=ACCENT,
            foreground=TEXT,
            borderwidth=0,
        )
        s.map(
            "TButton",
            background=[("active", ACCENT_HOVER), ("disabled", "#EBE3DF")],
            foreground=[("disabled", TEXT_SOFT)],
        )
        s.configure(
            "Primary.TButton",
            background=PRIMARY,
            foreground=TEXT,
            font=(FONTE, 9, "bold"),
        )
        s.map("Primary.TButton", background=[("active", PRIMARY_HOVER)])
        s.configure(
            "Danger.TButton",
            background="#F5D7D7",
            foreground="#A35B66",
        )
        s.map("Danger.TButton", background=[("active", "#EEC4C4")])
        s.configure(
            "Treeview",
            background=PANEL,
            fieldbackground=PANEL,
            foreground=TEXT,
            rowheight=30,
            font=(FONTE, 10),
            borderwidth=0,
        )
        s.configure(
            "Treeview.Heading",
            background="#F7E9E2",
            foreground=TEXT,
            font=(FONTE, 9, "bold"),
            relief="flat",
            padding=(8, 5),
        )
        s.map("Treeview", background=[("selected", "#F8DEC0")],
              foreground=[("selected", TEXT)])
        s.configure(
            "TCombobox",
            fieldbackground=PANEL,
            background=PANEL,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=LINE,
            padding=4,
        )
        s.configure(
            "TEntry",
            fieldbackground=PANEL,
            foreground=TEXT,
            bordercolor=LINE,
            padding=5,
        )
        s.configure(
            "Ph.TEntry",
            fieldbackground=PANEL,
            foreground=TEXT_SOFT,
            bordercolor=LINE,
            padding=5,
        )
        s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(6, 6, 6, 0))
        s.configure("Panel.TCheckbutton", background=PANEL, foreground=TEXT)
        s.configure(
            "TNotebook.Tab",
            background="#F7E9E2", foreground=TEXT,
            padding=(16, 7), borderwidth=0,
        )
        s.map(
            "TNotebook.Tab",
            background=[("selected", PANEL)],
            foreground=[("selected", HIGH)],
        )

    # ---------- placeholders (texto cinza) ----------
    def _setup_placeholder(self, entry, var, texto):
        entry._ph_text = texto
        entry._ph_ativo = False

        def ativar():
            entry._ph_ativo = True
            try:
                entry.configure(style="Ph.TEntry")
            except Exception:
                pass
            var.set(texto)

        def desativar():
            entry._ph_ativo = False
            try:
                entry.configure(style="TEntry")
            except Exception:
                pass
            var.set("")

        def on_in(_):
            if entry._ph_ativo:
                desativar()

        def on_out(_):
            if not (var.get() or "").strip():
                ativar()

        def on_var(*_):
            v = (var.get() or "")
            if v:
                if entry._ph_ativo and v != texto:
                    entry._ph_ativo = False
                    try:
                        entry.configure(style="TEntry")
                    except Exception:
                        pass
            else:
                if not entry._ph_ativo and entry.focus_get() != entry:
                    ativar()

        entry.bind("<FocusIn>", on_in)
        entry.bind("<FocusOut>", on_out)
        var.trace_add("write", on_var)
        ativar()

    def _valor_real(self, entry, var):
        if getattr(entry, "_ph_ativo", False):
            return ""
        return var.get()

    # ---------- construção da UI ----------
    def _build_ui(self):
        self.root.title("✦ Tarefas Diárias ✦")
        self.root.geometry("780x600")
        self.root.minsize(680, 500)
        self.root.configure(bg=BG)
        if os.path.exists(ICONE):
            try:
                self.root.iconbitmap(ICONE)
            except Exception:
                pass

        # Barra de título estilo janelinha XP
        barra = tk.Frame(self.root, bg=TITLEBAR)
        barra.pack(fill="x")
        ttk.Label(
            barra, text="  ✿  Tarefas Diárias  ✿  ",
            background=TITLEBAR, foreground=TITLEBAR_TEXT,
            font=(FONTE, 11, "bold"),
        ).pack(side="left", pady=3)
        self.lbl_data = ttk.Label(
            barra, text="", background=TITLEBAR,
            foreground=TITLEBAR_TEXT, font=(FONTE, 9),
        )
        self.lbl_data.pack(side="right", padx=10, pady=3)

        self.lbl_versao = ttk.Label(
            barra, text=VERSAO_LABEL, background=TITLEBAR,
            foreground=TITLEBAR_TEXT, font=(FONTE, 8),
        )
        self.lbl_versao.pack(side="right", padx=(0, 10), pady=3)

        # Bandeirinha pastel (como no Mini PC XP)
        faixa = tk.Frame(self.root, height=6)
        faixa.pack(fill="x")
        for i, cor in enumerate(STRIPE):
            tk.Frame(faixa, bg=cor, width=200, height=6).pack(side="left", expand=True, fill="x")

        corpo = ttk.Frame(self.root, padding=12)
        corpo.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(corpo)
        self.notebook.pack(fill="both", expand=True)

        # ---- aba: tarefas ----
        aba_tarefas = ttk.Frame(self.notebook, style="Panel.TFrame", padding=0)
        self.notebook.add(aba_tarefas, text="✿  Tarefas")

        self.lbl_progresso = ttk.Label(
            aba_tarefas, text="", background=BG, foreground=TEXT_SOFT, font=(FONTE, 9)
        )
        self.lbl_progresso.pack(anchor="w", pady=(0, 8))

        # ---- barra de adicionar ----
        addbar = ttk.Frame(aba_tarefas, style="Panel.TFrame", padding=8)
        addbar.pack(fill="x", pady=(0, 8))

        self.var_titulo = tk.StringVar()
        self.ent_titulo = ttk.Entry(addbar, textvariable=self.var_titulo, font=(FONTE, 10))
        self.ent_titulo.pack(side="left", fill="x", expand=True, ipady=3)
        self._setup_placeholder(self.ent_titulo, self.var_titulo, "Escreva a tarefa…")

        self.var_data = tk.StringVar()
        self.ent_data = ttk.Entry(
            addbar, textvariable=self.var_data, width=11,
            font=(FONTE, 10),
        )
        self.ent_data.pack(side="left", padx=(8, 0), ipady=3)
        self._setup_placeholder(self.ent_data, self.var_data, "dd/mm/aaaa")

        self.var_prio = tk.StringVar(value="Média")
        ttk.Combobox(
            addbar, textvariable=self.var_prio, width=7, state="readonly",
            values=["Baixa", "Média", "Alta"], font=(FONTE, 10),
        ).pack(side="left", padx=(8, 0))

        self.var_categoria = tk.StringVar(value="Pessoal")
        ttk.Combobox(
            addbar, textvariable=self.var_categoria, width=10,
            values=self.categorias_padrao, font=(FONTE, 10),
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            addbar, text="＋ Adicionar", style="Primary.TButton",
            command=self._adicionar,
        ).pack(side="left", padx=(8, 0))

        dica = "dd/mm/aaaa · opcional · categoria (empresa, jogos…) · Enter adiciona · Duplo clique edita · Delete apaga"
        ttk.Label(addbar, text=dica, background=PANEL, foreground=TEXT_SOFT,
                  font=(FONTE, 8)).pack(side="bottom", anchor="w", pady=(4, 0))

        # ---- barra de filtro/busca ----
        filtro = ttk.Frame(aba_tarefas, style="Panel.TFrame", padding=(8, 6))
        filtro.pack(fill="x", pady=(0, 8))

        ttk.Button(filtro, text="✓  Concluir", style="TButton",
                   command=self._alternar, width=11).pack(side="left")
        ttk.Button(filtro, text="✎  Editar", style="TButton",
                   command=self._editar, width=9).pack(side="left", padx=4)
        ttk.Button(filtro, text="🗑  Excluir", style="Danger.TButton",
                   command=self._excluir, width=9).pack(side="left")

        self.var_cat_filtro = tk.StringVar(value="Todas")
        self.cbx_cat_filtro = ttk.Combobox(
            filtro, textvariable=self.var_cat_filtro, width=12, state="readonly",
            values=["Todas"] + self.categorias_padrao, font=(FONTE, 9),
        )
        self.cbx_cat_filtro.pack(side="right", padx=(6, 0))

        self.var_filtro = tk.StringVar(value="Todas")
        ttk.Combobox(
            filtro, textvariable=self.var_filtro, width=9, state="readonly",
            values=["Todas", "Pendentes", "Concluídas"], font=(FONTE, 9),
        ).pack(side="right", padx=(6, 0))

        self.var_busca = tk.StringVar()
        self.ent_busca = ttk.Entry(
            filtro, textvariable=self.var_busca, width=16, font=(FONTE, 9),
        )
        self.ent_busca.pack(side="right")
        self._setup_placeholder(self.ent_busca, self.var_busca, "Buscar…")

        # ---- lista de tarefas ----
        lista_wrap = ttk.Frame(aba_tarefas, style="Panel.TFrame", padding=0)
        lista_wrap.pack(fill="both", expand=True)

        cols = ("feita", "titulo", "categoria", "data", "prazo", "prioridade")
        self.tree = ttk.Treeview(lista_wrap, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("feita", text="")
        self.tree.column("feita", width=34, anchor="center", stretch=False)
        self.tree.heading("titulo", text="Tarefa")
        self.tree.column("titulo", width=300, anchor="w")
        self.tree.heading("categoria", text="Categoria")
        self.tree.column("categoria", width=90, anchor="w", stretch=False)
        self.tree.heading("data", text="Data")
        self.tree.column("data", width=80, anchor="center", stretch=False)
        self.tree.heading("prazo", text="Prazo")
        self.tree.column("prazo", width=100, anchor="center", stretch=False)
        self.tree.heading("prioridade", text="Prioridade")
        self.tree.column("prioridade", width=80, anchor="center", stretch=False)

        sb = ttk.Scrollbar(lista_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        sb.pack(side="right", fill="y", padx=(0, 8), pady=8)

        # ---- rodapé de ações ----
        rodape = ttk.Frame(aba_tarefas, style="Panel.TFrame", padding=(8, 8))
        rodape.pack(fill="x", pady=(8, 0))

        self.lbl_count = ttk.Label(rodape, text="", background=PANEL,
                                   foreground=TEXT_SOFT, font=(FONTE, 9))
        self.lbl_count.pack(side="left")

        ttk.Button(rodape, text="🖨  Imprimir", style="TButton",
                   command=self._abrir_impressao).pack(side="right", padx=(4, 0))
        ttk.Button(rodape, text="⤓ Importar", style="TButton",
                   command=self._importar).pack(side="right", padx=(4, 0))
        ttk.Button(rodape, text="⤒ Exportar", style="TButton",
                   command=self._exportar).pack(side="right", padx=(4, 0))
        ttk.Button(rodape, text="Limpar feitas", style="TButton",
                   command=self._limpar_feitas).pack(side="right", padx=(4, 0))

        # ---- aba: texto livre ----
        aba_texto = ttk.Frame(self.notebook, style="Panel.TFrame", padding=8)
        self.notebook.add(aba_texto, text="🖨  Texto livre")
        self._build_tab_texto(aba_texto)

    def _bind(self):
        self.ent_titulo.bind("<Return>", lambda e: self._adicionar())
        self.var_busca.trace_add("write", lambda *a: self.atualizar())
        self.var_filtro.trace_add("write", lambda *a: self.atualizar())
        self.var_cat_filtro.trace_add("write", lambda *a: self.atualizar())
        self.tree.bind("<Double-1>", lambda e: self._editar())
        self.tree.bind("<space>", lambda e: self._alternar())
        self.root.bind("<Delete>", lambda e: self._excluir())

    # ---------- dados ----------
    def _arquivo(self):
        return ARQ_PADRAO

    def _carregar(self):
        arq = self._arquivo()
        if os.path.exists(arq):
            try:
                with open(arq, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.tarefas = dados.get("tarefas", []) if isinstance(dados, dict) else dados
            except Exception:
                self.tarefas = []
        if not isinstance(self.tarefas, list):
            self.tarefas = []

    def _salvar(self):
        try:
            with open(self._arquivo(), "w", encoding="utf-8") as f:
                json.dump({"tarefas": self.tarefas}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def _proximo_id(self):
        usados = {t["id"] for t in self.tarefas if isinstance(t.get("id"), str)}
        n = 1
        while str(n) in usados:
            n += 1
        return str(n)

    # ---------- operações ----------
    def _adicionar(self):
        titulo = self._valor_real(self.ent_titulo, self.var_titulo).strip()
        if not titulo:
            messagebox.showinfo("Tarefa", "Escreva o título da tarefa.")
            return
        d_iso = self._ler_data_entry()
        if d_iso is None:
            return
        categoria = (self.var_categoria.get() or "Pessoal").strip() or "Pessoal"
        self.tarefas.append({
            "id": self._proximo_id(),
            "titulo": titulo,
            "categoria": categoria,
            "data": d_iso,
            "prioridade": self.var_prio.get().lower(),
            "concluida": False,
            "criada_em": datetime.datetime.now().isoformat(timespec="seconds"),
            "concluida_em": "",
        })
        self.var_titulo.set("")
        self._salvar()
        self.atualizar()
        self.ent_titulo.focus_set()

    def _ler_data_entry(self):
        texto = self._valor_real(self.ent_data, self.var_data).strip()
        if not texto:
            return ""
        fmt = "%d/%m/%Y"
        try:
            d = datetime.datetime.strptime(texto, fmt).date()
            return d.isoformat()
        except ValueError:
            messagebox.showerror(
                "Data inválida",
                "Use o formato dd/mm/aaaa, por exemplo 25/12/2026.\n"
                "Deixe o campo vazio para não definir prazo.",
            )
            return None

    def _selecionada(self):
        sel = self.tree.selection()
        if not sel:
            return None
        i = int(sel[0])
        if 0 <= i < len(self._linhas_atuais()):
            return self._linhas_atuais()[i]
        return None

    def _linhas_atuais(self):
        # ordena: pendentes primeiro (por categoria e data), depois concluídas
        def chave(t):
            pr = {"alta": 0, "media": 1, "baixa": 2}.get((t.get("prioridade") or "media").lower(), 1)
            d = t.get("data") or "9999-99-99"
            cat = (t.get("categoria") or "").strip().upper() or "zzz"
            concluida = 1 if t.get("concluida") else 0
            concluida_em = t.get("concluida_em") or ""
            return (concluida, cat, d, pr, concluida_em)
        return sorted(self._filtradas(), key=chave)

    def _filtradas(self):
        b = (self.busca or "").strip().lower()
        cat = (self.var_cat_filtro.get() if hasattr(self, "var_cat_filtro") else "Todas") or "Todas"
        saida = []
        for t in self.tarefas:
            if self.filtro == "Pendentes" and t.get("concluida"):
                continue
            if self.filtro == "Concluídas" and not t.get("concluida"):
                continue
            if b and b not in (t.get("titulo") or "").lower():
                continue
            if cat not in ("Todas", "") and (t.get("categoria") or "") != cat:
                continue
            saida.append(t)
        return saida

    def _categorias_em_uso(self):
        usados = []
        for t in self.tarefas:
            c = (t.get("categoria") or "").strip()
            if c and c not in usados:
                usados.append(c)
        usados.sort(key=str.lower)
        return usados

    def _alternar(self, *_):
        t = self._selecionada()
        if not t:
            return
        t["concluida"] = not t.get("concluida")
        t["concluida_em"] = datetime.datetime.now().isoformat(timespec="seconds") if t["concluida"] else ""
        self._salvar()
        self.tree.selection_set((self._pos_na_lista(t),))
        self.atualizar()

    def _pos_na_lista(self, t):
        linhas = self._linhas_atuais()
        for i, x in enumerate(linhas):
            if x.get("id") == t.get("id"):
                return str(i)
        return "0"

    def _editar(self, *_):
        t = self._selecionada()
        if not t:
            return
        self._form(t)

    def _excluir(self, *_):
        t = self._selecionada()
        if not t:
            return
        if not messagebox.askyesno(
            "Excluir tarefa",
            "Excluir a tarefa:\n  “%s”?" % t.get("titulo", ""),
        ):
            return
        self.tarefas = [x for x in self.tarefas if x.get("id") != t.get("id")]
        self._salvar()
        self.atualizar()

    def _limpar_feitas(self):
        feitas = [t for t in self.tarefas if t.get("concluida")]
        if not feitas:
            return
        if not messagebox.askyesno(
            "Limpar concluídas",
            "Remover %d tarefa(s) já concluída(s)?" % len(feitas),
        ):
            return
        self.tarefas = [t for t in self.tarefas if not t.get("concluida")]
        self._salvar()
        self.atualizar()

    def _exportar(self):
        caminho = filedialog.asksaveasfilename(
            parent=self.root,
            title="Exportar tarefas",
            defaultextension=".json",
            initialfile="tarefas_diarias_%s.json" % datetime.date.today().isoformat(),
            filetypes=[("JSON", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump({"tarefas": self.tarefas}, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Exportar", "Tarefas exportadas com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro ao exportar", str(e))

    def _importar(self):
        caminho = filedialog.askopenfilename(
            parent=self.root,
            title="Importar tarefas",
            filetypes=[("JSON", "*.json"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            novos = dados.get("tarefas", []) if isinstance(dados, dict) else dados
            if not isinstance(novos, list):
                raise ValueError("arquivo sem a lista de tarefas")
        except Exception as e:
            messagebox.showerror("Importar", "Não dá pra ler esse arquivo:\n%s" % e)
            return
        for t in novos:
            t.setdefault("concluida", False)
            t.setdefault("prioridade", "media")
            t.setdefault("data", "")
            t.setdefault("categoria", "")
        modo = messagebox.askquestion(
            "Importar",
            "Importar %d tarefa(s).\n\nSubstituir a lista atual ou mesclar com ela?"  % len(novos),
            icon="question",
        )
        if modo == "yes":  # substituir
            self.tarefas = novos
        else:  # mesclar por id
            por_id = {t.get("id"): t for t in self.tarefas}
            for t in novos:
                if not t.get("id"):
                    continue
                if t["id"] in por_id and por_id[t["id"]] is not t:
                    por_id[t["id"]] = t  # sobrescreve
                else:
                    por_id[t.get("id", "")] = t
            self.tarefas = list(por_id.values())
        self._salvar()
        self.atualizar()
        messagebox.showinfo("Importar", "Pronto! Tarefas importadas.")

    def _abrir_impressao(self):
        quants = {
            "pendentes": len([t for t in self.tarefas if not t.get("concluida")]),
            "concluidas": len([t for t in self.tarefas if t.get("concluida")]),
            "todas": len(self.tarefas),
        }
        if not quants["todas"]:
            messagebox.showinfo("Imprimir", "Nenhuma tarefa pra imprimir.")
            return
        if not impressora_sc03.disponivel():
            messagebox.showwarning(
                "Impressora não detectada",
                "Impressora não detectada.\n\n"
                "Conecte a impressora SC03 via Bluetooth e tente novamente.\n\n"
                "Pode exportar as tarefas em JSON e imprimir depois.",
            )
            return
        win = tk.Toplevel(self.root)
        win.title("Imprimir tarefas ✿")
        win.configure(bg=PANEL)
        win.resizable(False, False)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        frm = ttk.Frame(win, style="Panel.TFrame", padding=16)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Imprimir tarefas na SC03:",
                  background=PANEL, font=(FONTE, 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(frm, text="Incluir:", background=PANEL).grid(row=1, column=0, sticky="e", pady=10)
        v_quais = tk.StringVar(value="Pendentes")
        ttk.Combobox(frm, textvariable=v_quais, state="readonly",
                     values=["Pendentes (%d)" % quants["pendentes"],
                             "Concluídas (%d)" % quants["concluidas"],
                             "Todas (%d)" % quants["todas"]],
                     width=18).grid(row=1, column=1, sticky="w", pady=10)
        v_grupo = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Listar por categoria", variable=v_grupo,
                        style="Panel.TCheckbutton"
                        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(frm, text="Intensidade:", background=PANEL).grid(row=3, column=0, sticky="e", pady=(0, 10))
        v_preset = tk.StringVar(value="forte")
        ttk.Combobox(frm, textvariable=v_preset, state="readonly", values=list(impressora_sc03.PRESETS.keys()),
                     width=8).grid(row=3, column=1, sticky="w", pady=(0, 10))
        ttk.Label(frm, text="Tamanho da letra (cm):", background=PANEL).grid(row=4, column=0, sticky="e", pady=(0, 14))
        v_cm = tk.StringVar(value="0,30")
        ttk.Combobox(frm, textvariable=v_cm, state="readonly",
                     values=["0,15 (letra pequena)", "0,30 (letra média)", "0,48 (letra grande)"],
                     width=24).grid(row=4, column=1, sticky="w", pady=(0, 14))
        b = ttk.Button(frm, text="🖨  Imprimir agora", style="Primary.TButton",
                       command=lambda: self._print(win, v_quais.get(), v_grupo.get(), v_preset.get(), v_cm.get()))
        b.grid(row=5, column=0, columnspan=2, pady=(0, 4))

    def _colunas_por_cm(self, cm_str):
        try:
            cm = float(cm_str.split()[0].replace(",", "."))
        except Exception:
            return 32
        if cm >= 0.41:
            return 10
        if cm >= 0.25:
            return 16
        return 32

    @staticmethod
    def _quais_combo(rotulo):
        r = (rotulo or "").lower()
        if r.startswith("conclu"):
            return "concluidas"
        if r.startswith("todas"):
            return "todas"
        return "pendentes"

    def _linhas_largas(self, colunas, quais="pendentes", por_categoria=False):
        longas = []
        for linha in impressora_sc03.montar_linhas(self.tarefas, quais=quais, por_categoria=por_categoria):
            if len(linha) > colunas:
                longas.append(linha)
        return longas

    def _print(self, win, quais_rotulo, por_categoria, preset, cm_str):
        win.destroy()
        colunas = self._colunas_por_cm(cm_str)
        quais = self._quais_combo(quais_rotulo)
        largas = self._linhas_largas(colunas, quais=quais, por_categoria=por_categoria)
        if largas:
            pre = "\n".join("•  …%s" % linha for linha in largas)
            aviso = (
                "%d linha(s) não cabem em 1 linha com essa letra (%.2f cm):\n\n%s\n\n"
                "Use uma letra menor pra caber 1 por linha,\n"
                "ou continue mesmo assim (a linha vai quebrar).\n\n"
                "Continuar a impressão?"
            ) % (len(largas), float(cm_str.split()[0].replace(",", ".")), pre)
            if not messagebox.askyesno("Aviso de impressão", aviso):
                self.root.after(0, self._abrir_impressao)
                return
        ok, msg = impressora_sc03.imprimir_tarefas(
            self.tarefas, quais=quais, por_categoria=por_categoria, preset=preset, colunas=colunas
        )
        if ok:
            messagebox.showinfo("Impressão", "Tarefas enviadas pra impressora SC03.\n\n" + (msg or ""))
        else:
            messagebox.showerror("Falha na impressão", msg)

    # ---------- aba: texto livre ----------
    def _build_tab_texto(self, parent):
        editor_wrap = ttk.Frame(parent, style="Panel.TFrame")
        editor_wrap.pack(fill="x", pady=(0, 6))

        self.txt_livre = tk.Text(
            editor_wrap, font=(FONTE, 10), bg="#FFFFFF", fg=TEXT, relief="flat",
            wrap="word", undo=True, padx=10, pady=8, height=8,
        )
        sb = ttk.Scrollbar(editor_wrap, orient="vertical", command=self.txt_livre.yview)
        self.txt_livre.configure(yscrollcommand=sb.set)
        self.txt_livre.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.txt_livre.insert("1.0", TXT_PLACEHOLDER)
        self.txt_livre.configure(fg=TEXT_SOFT)
        self.txt_livre.edit_modified(False)
        self._txt_placeholder_on = True
        self.txt_livre.bind("<FocusIn>", self._on_txt_in)
        self.txt_livre.bind("<FocusOut>", self._on_txt_out)
        self.txt_livre.bind("<<Modified>>", self._on_txt_modificado)

        controles = ttk.Frame(parent, style="Panel.TFrame", padding=(2, 2))
        controles.pack(fill="x", pady=(0, 6))

        ttk.Label(controles, text="Intensidade:", background=PANEL,
                  foreground=TEXT).pack(side="left")
        self.var_preset_texto = tk.StringVar(value="forte")
        ttk.Combobox(controles, textvariable=self.var_preset_texto, state="readonly",
                     values=list(impressora_sc03.PRESETS.keys()), width=7
                     ).pack(side="left", padx=(4, 12))

        ttk.Label(controles, text="Tamanho da letra:", background=PANEL,
                  foreground=TEXT).pack(side="left")
        self.var_cm_texto = tk.StringVar(value="0,30 (letra média)")
        ttk.Combobox(controles, textvariable=self.var_cm_texto, state="readonly",
                     values=["0,15 (letra pequena)", "0,30 (letra média)", "0,48 (letra grande)"],
                     width=20).pack(side="left", padx=(4, 12))

        ttk.Button(controles, text="✓ Atualizar preview",
                   command=self._preview_texto).pack(side="left")
        ttk.Button(controles, text="🖨  Imprimir", style="Primary.TButton",
                   command=self._imprimir_texto).pack(side="left", padx=(6, 0))

        self.lbl_folha = ttk.Label(controles, text="", background=PANEL,
                                   foreground=TEXT_SOFT, font=(FONTE, 9))
        self.lbl_folha.pack(side="right", padx=(6, 0))

        prev_host = ttk.Frame(parent, style="Panel.TFrame")
        prev_host.pack(fill="both", expand=True)
        self.pv = tk.Canvas(prev_host, bg="#EADCD5", highlightthickness=0)
        sbv = ttk.Scrollbar(prev_host, orient="vertical", command=self.pv.yview)
        sbh = ttk.Scrollbar(prev_host, orient="horizontal", command=self.pv.xview)
        self.pv.configure(yscrollcommand=sbv.set, xscrollcommand=sbh.set)
        self.pv.grid(row=0, column=0, sticky="nsew")
        sbv.grid(row=0, column=1, sticky="ns")
        sbh.grid(row=1, column=0, sticky="ew")
        prev_host.rowconfigure(0, weight=1)
        prev_host.columnconfigure(0, weight=1)

        self._pv_font_cache = {}
        self._pv_job = None
        self.var_cm_texto.trace_add("write", lambda *a: self._agendar_preview())
        self._preview_texto()

    def _texto_livre(self):
        if getattr(self, "_txt_placeholder_on", False):
            return ""
        return self.txt_livre.get("1.0", "end-1c")

    def _on_txt_in(self, _=None):
        if self._txt_placeholder_on:
            self.txt_livre.delete("1.0", "end")
            self.txt_livre.configure(fg=TEXT)
            self.txt_livre.edit_modified(False)
            self._txt_placeholder_on = False

    def _on_txt_out(self, _=None):
        atual = self.txt_livre.get("1.0", "end-1c")
        if not atual.strip():
            self.txt_livre.delete("1.0", "end")
            self.txt_livre.insert("1.0", TXT_PLACEHOLDER)
            self.txt_livre.configure(fg=TEXT_SOFT)
            self.txt_livre.edit_modified(False)
            self._txt_placeholder_on = True
            self._preview_texto()

    def _on_txt_modificado(self, _=None):
        if not self.txt_livre.edit_modified():
            return
        self.txt_livre.edit_modified(False)
        self._agendar_preview()

    def _agendar_preview(self):
        if self._pv_job:
            try:
                self.root.after_cancel(self._pv_job)
            except Exception:
                pass
        self._pv_job = self.root.after(350, self._preview_texto)

    @staticmethod
    def _largura_visual(s, tabstop=4):
        # largura em colunas de fonte monoespaçada; tab avança até o próximo tabstop
        w = 0
        for ch in s:
            if ch == "\t":
                w += tabstop - (w % tabstop)
            else:
                w += 1
        return w

    def _quebrar_linhas(self, texto, colunas):
        limite = int(colunas)
        tabstop = 4
        saida = []
        for par in texto.split("\n"):
            atual = ""
            for ch in par:
                add = tabstop - (self._largura_visual(atual, tabstop) % tabstop) if ch == "\t" else 1
                if atual and self._largura_visual(atual, tabstop) + add > limite:
                    saida.append(atual)
                    atual = ""
                if ch == "\t":
                    add = tabstop - (self._largura_visual(atual, tabstop) % tabstop)
                    atual += " " * add  # expande o tab em espaços (fonte monoespaçada)
                else:
                    atual += ch
            saida.append(atual)
        while saida and saida[-1] == "":
            saida.pop()
        return saida or [""]

    def _font_mono_bold(self, target_px):
        chave = int(round(target_px * 4))
        f = self._pv_font_cache.get(chave)
        if f is not None:
            return f
        fam = "Consolas" if "Consolas" in tkfont.families(self.root) else "Courier New"
        base = tkfont.Font(root=self.root, family=fam, weight="bold")
        h0 = int(max(8, target_px / 0.55))
        melhor = (1e9, 8)
        for h in range(max(4, h0 - 10), h0 + 11):
            base.configure(size=-h)
            m = base.measure("M")
            d = abs(m - target_px)
            if d < melhor[0]:
                melhor = (d, h)
        base.configure(size=-melhor[1])
        self._pv_font_cache[chave] = base
        return base

    def _preview_texto(self):
        if not hasattr(self, "pv"):
            return
        colunas = self._colunas_por_cm(self.var_cm_texto.get())
        cell_px = {32: 12, 16: 24, 10: 38}[colunas]
        texto = self._texto_livre()
        linhas = self._quebrar_linhas(texto, colunas) if texto.strip() else [""]

        mm2px = self.ppi / 25.4
        escala = (PRINT_W_MM * mm2px) / PRINT_W_PX
        cell = cell_px * escala
        passo = cell * 1.4
        papel_w = PAPEL_W_MM * mm2px
        impr_w = PRINT_W_MM * mm2px
        margem = (papel_w - impr_w) / 2.0

        conteudo_px = len(linhas) * passo
        if linhas and linhas != [""]:
            papel_h = max(conteudo_px + passo + 24.0, 48.0)
        else:
            papel_h = 48.0
        cm_total = (papel_h / mm2px) / 10.0
        self.lbl_folha.configure(text="Folha: 58 mm × %.1f cm · margem 5 mm" % cm_total)

        topo = 30.0
        esq = 40.0
        x0 = esq
        y0 = topo
        xp = x0 + margem
        xp2 = xp + impr_w

        c = self.pv
        c.delete("all")

        c.create_rectangle(0, 0, x0 + papel_w + 40, y0 + papel_h + 40, fill="#EADCD5", outline="")
        c.create_rectangle(x0, y0, x0 + papel_w, y0 + papel_h, fill="#F2E6E0", outline="#C9B4AC")
        c.create_rectangle(x0, y0, xp, y0 + papel_h, fill="#F6EDE8", outline="")
        c.create_rectangle(xp2, y0, x0 + papel_w, y0 + papel_h, fill="#F6EDE8", outline="")
        c.create_rectangle(xp, y0, xp2, y0 + papel_h, fill="#FFFFFF", outline="#D8C6BE")

        c.create_line(xp, y0, xp, y0 + papel_h, fill="#E88A98", dash=(3, 3))
        c.create_line(xp2, y0, xp2, y0 + papel_h, fill="#E88A98", dash=(3, 3))
        c.create_text(x0 + margem / 2, y0 + 10, text="5mm",
                      fill="#C9A9A0", font=(FONTE, 7), anchor="n")
        c.create_text(xp2 + margem / 2, y0 + 10, text="5mm",
                      fill="#C9A9A0", font=(FONTE, 7), anchor="n")

        cor_grid = "#F2DFE0"
        xmm = 10.0
        while xmm < PRINT_W_MM - 0.01:
            gx = xp + xmm * mm2px
            c.create_line(gx, y0, gx, y0 + papel_h, fill=cor_grid, dash=(2, 3))
            xmm += 10.0
        ymm = 10.0
        while ymm * mm2px < papel_h:
            gy = y0 + ymm * mm2px
            c.create_line(xp, gy, xp2, gy, fill=cor_grid, dash=(2, 3))
            ymm += 10.0

        c.create_rectangle(x0, y0 - 22, x0 + papel_w, y0, fill="#F7E9E2", outline="#EADCD5")
        mmi = 0.0
        while mmi <= PAPEL_W_MM + 0.01:
            rx = x0 + mmi * mm2px
            if int(round(mmi)) % 10 == 0:
                c.create_line(rx, y0 - 22, rx, y0, fill="#B49B8F")
                c.create_text(rx, y0 - 24, text=str(int(round(mmi)) // 10),
                              fill="#8C6F64", font=(FONTE, 7), anchor="s")
            else:
                c.create_line(rx, y0 - 14, rx, y0, fill="#C9B4AC")
            mmi += 5.0

        c.create_rectangle(x0 - 24, y0, x0 - 8, y0 + papel_h, fill="#F7E9E2", outline="#EADCD5")
        my = 0.0
        while my * mm2px <= papel_h + 0.01:
            ry = y0 + my * mm2px
            if int(round(my)) % 10 == 0:
                c.create_line(x0 - 24, ry, x0 - 8, ry, fill="#B49B8F")
                c.create_text(x0 - 28, ry, text=str(int(round(my)) // 10),
                              fill="#8C6F64", font=(FONTE, 7), anchor="e")
            else:
                c.create_line(x0 - 24, ry, x0 - 14, ry, fill="#C9B4AC")
            my += 5.0

        if linhas and linhas != [""]:
            fonte = self._font_mono_bold(cell)
            yt = y0
            for linha in linhas:
                if linha:
                    c.create_text(xp, yt, text=linha, anchor="nw", fill="#4A3228", font=fonte)
                yt += passo

        w = int(x0 + papel_w + 28)
        h = int(y0 + papel_h + 20)
        c.configure(width=min(w, 620), height=min(h, 460))
        c.configure(scrollregion=(0, 0, w, h))
        c.yview_moveto(0)
        c.xview_moveto(0)

    def _imprimir_texto(self):
        texto = self._texto_livre()
        if not texto.strip():
            messagebox.showinfo("Texto livre", "Escreva o texto antes de imprimir.")
            return
        if not impressora_sc03.disponivel():
            messagebox.showwarning(
                "Impressora não detectada",
                "Impressora SC03 não detectada.\n\n"
                "Conecte a impressora via Bluetooth e tente novamente.",
            )
            return
        colunas = self._colunas_por_cm(self.var_cm_texto.get())
        preset = self.var_preset_texto.get()
        ok, msg = impressora_sc03.imprimir_texto(texto, preset=preset, colunas=colunas)
        if ok:
            messagebox.showinfo("Impressão", "Texto enviado pra impressora SC03.\n\n" + (msg or ""))
        else:
            messagebox.showerror("Falha na impressão", msg)

    # ---------- formulário de edição ----------
    def _form(self, t):
        win = tk.Toplevel(self.root)
        win.title("Editar tarefa ✎")
        win.configure(bg=PANEL)
        win.resizable(False, False)
        try:
            win.transient(self.root)
            win.grab_set()
        except Exception:
            pass
        frm = ttk.Frame(win, style="Panel.TFrame", padding=16)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="Editar tarefa ✎", background=PANEL,
                  font=(FONTE, 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(frm, text="Título:", background=PANEL).grid(row=1, column=0, sticky="e", pady=4)
        v_titulo = tk.StringVar(value=t.get("titulo", ""))
        ent_titulo = ttk.Entry(frm, textvariable=v_titulo, width=32, font=(FONTE, 10))
        ent_titulo.grid(row=1, column=1, sticky="w", pady=4)
        self._setup_placeholder(ent_titulo, v_titulo, "Título da tarefa")

        ttk.Label(frm, text="Data (dd/mm/aaaa):", background=PANEL).grid(row=2, column=0, sticky="e", pady=4)
        v_data = tk.StringVar(value=data_exibir(t.get("data", "")) if t.get("data") else "")
        ent_data = ttk.Entry(frm, textvariable=v_data, width=14, font=(FONTE, 10))
        ent_data.grid(row=2, column=1, sticky="w", pady=4)
        self._setup_placeholder(ent_data, v_data, "dd/mm/aaaa")

        ttk.Label(frm, text="Prioridade:", background=PANEL).grid(row=3, column=0, sticky="e", pady=4)
        v_prio = tk.StringVar(value=(t.get("prioridade") or "media").capitalize())
        ttk.Combobox(frm, textvariable=v_prio, state="readonly", values=["Baixa", "Média", "Alta"],
                     width=10).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="Categoria:", background=PANEL).grid(row=4, column=0, sticky="e", pady=4)
        v_cat = tk.StringVar(value=t.get("categoria", "") or "")
        cats_edit = self._categorias_em_uso()
        for c in self.categorias_padrao:
            if c not in cats_edit:
                cats_edit.append(c)
        ttk.Combobox(frm, textvariable=v_cat, values=cats_edit,
                     width=14).grid(row=4, column=1, sticky="w", pady=4)

        def salvar():
            titulo = self._valor_real(ent_titulo, v_titulo).strip()
            if not titulo:
                messagebox.showinfo("Editar", "O título não pode ficar vazio.")
                return
            d_iso = self._ler_data_de(self._valor_real(ent_data, v_data))
            if d_iso is None:
                return
            t["titulo"] = titulo
            t["data"] = d_iso
            t["prioridade"] = v_prio.get().lower()
            t["categoria"] = (v_cat.get() or "").strip()
            self._salvar()
            self.atualizar()
            win.destroy()

        ttk.Button(frm, text="Salvar", style="Primary.TButton", command=salvar).grid(row=6, column=0, pady=(14, 0))
        ttk.Button(frm, text="Cancelar", command=win.destroy).grid(row=6, column=1, pady=(14, 0))

    def _ler_data_de(self, texto):
        texto = (texto or "").strip()
        if not texto:
            return ""
        try:
            return datetime.datetime.strptime(texto, "%d/%m/%Y").date().isoformat()
        except ValueError:
            messagebox.showerror("Data inválida", "Use o formato dd/mm/aaaa.")
            return None

    # ---------- atualização da tela ----------
    def atualizar(self):
        self.filtro = self.var_filtro.get()
        self.busca = self._valor_real(self.ent_busca, self.var_busca)
        self.tree.delete(*self.tree.get_children())

        pendentes = [t for t in self.tarefas if not t.get("concluida")]
        feitas = len(self.tarefas) - len(pendentes)
        hoje = datetime.date.today()

        for i, t in enumerate(self._linhas_atuais()):
            concluida = t.get("concluida")
            if concluida:
                marcador = "☑"
                tag = "concluida"
                prazo = "Concluída"
            else:
                marcador = "☐"
                tag = "p_" + (t.get("prioridade") or "media").lower()
                dias = dias_ate(t.get("data") or "")
                if t.get("data"):
                    if dias is not None and dias < 0:
                        tag = "atrasada"
                        prazo = "● Atrasada %d d" % abs(dias)
                    elif dias == 0:
                        tag = "hoje"
                        prazo = "● Vence hoje"
                    elif dias <= 2:
                        prazo = "Faltam %d d" % dias
                    else:
                        prazo = ""
                else:
                    prazo = "sem prazo"
            prio = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}.get(
                (t.get("prioridade") or "media").lower(), "—")
            self.tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                marcador,
                t.get("titulo", ""),
                (t.get("categoria") or "") or "—",
                data_exibir(t.get("data", "")),
                prazo,
                prio,
            ))

        self._aplicar_tags()
        self._atualizar_categorias()
        self.lbl_data.configure(text=hoje.strftime("%A, %d/%m/%Y"))
        self.lbl_progresso.configure(
            text="✿ %d pendente(s) · %d concluída(s) hoje na lista"
                 % (len(pendentes), feitas)
        )
        total = len(self.tarefas)
        self.lbl_count.configure(
            text="Total: %d tarefa(s) · %d pendente(s) · %d concluída(s)"
                 % (total, len(pendentes), feitas)
        )
        self._estado_botoes()

    def _aplicar_tags(self):
        self.tree.tag_configure("p_alta", foreground=HIGH)
        self.tree.tag_configure("p_media", foreground=MED)
        self.tree.tag_configure("p_baixa", foreground=LOW)
        self.tree.tag_configure("atrasada", foreground=DANGER)
        self.tree.tag_configure("hoje", foreground=DANGER)
        self.tree.tag_configure("concluida", foreground=DONE)

    def _atualizar_categorias(self):
        opcoes = ["Todas"] + self._categorias_em_uso()
        for c in self.categorias_padrao:
            if c not in opcoes:
                opcoes.append(c)
        self.cbx_cat_filtro.configure(values=opcoes)
        if not (self.var_categoria.get() or "").strip():
            self.var_categoria.set("Pessoal")

    def _estado_botoes(self):
        return


def main():
    selftest = "--selftest" in sys.argv
    root = tk.Tk()
    app = TarefasApp(root)
    if selftest:
        root.after(2500, root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()