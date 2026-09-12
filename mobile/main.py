# -*- coding: utf-8 -*-
"""
main.py — Tarefas Diárias ✿ MOBILE (KivyMD)

Versão Android do app Tarefas Diárias (mesma lógica e formato JSON do desktop).
Roda SEM IA. Salva em tarefas.json no diretório privado do app.

Build do APK (Linux/WSL, com Buildozer):
    cd mobile
    buildozer init          # (já tem buildozer.spec aqui; não precisa)
    buildozer android debug

Instalação no celular:
    adb install bin/tarefasdiarias-*-debug.apk
ou copiar o .apk para o celular e instalar.

Dependências no computador de build:
    pip install buildozer cython
    (WSL2 + Ubuntu recomendado; buildozer não roda nativo no Windows)

Estrutura:
    mobile/
      main.py            <- este arquivo
      buildozer.spec     <- config do APK
      ../assets/app.png  <- ícone (apontado no spec)
"""

import datetime
import json
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton, MDRaisedButton, MDIconButton
from kivymd.uix.checkbox import MDCheckbox
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineAvatarListItem, TwoLineAvatarListItem, IconRightWidget
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

# ---------------------------------------------------------------------------
# Versão do app (mesma do desktop)
# ---------------------------------------------------------------------------
VERSAO = "1.1.0"
VERSAO_DATA = "2026-09-12"
VERSAO_LABEL = "v%s · %s" % (VERSAO, VERSAO_DATA)

# Cores pastel iguais ao desktop
BG = "#FDF6F2"
PRIMARY = "#FFB3A7"
PRIMARY_HOVER = "#FF9E90"
ACCENT = "#CBE6F7"
TEXT = "#5A4641"
TEXT_SOFT = "#9C8B85"
TITLEBAR = "#FFC9D6"

CATEGORIAS_PADRAO = ["Pessoal", "Empresa", "Estudos", "Jogos", "Outros"]
PRIORIDADES = ["Baixa", "Média", "Alta"]

KV = """
<ScreenManager>:
    TarefasScreen:
    TextoScreen:

<TarefasScreen>:
    name: "tarefas"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "✿ Tarefas Diárias ✿"
            md_bg_color: app.titlebar
            specific_text_color: app.text_color
            right_action_items: [["export", lambda x: app.exportar()], ["import", lambda x: app.importar()]]

        MDBoxLayout:
            orientation: "vertical"
            padding: dp(8)
            spacing: dp(6)

            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(56)
                spacing: dp(6)

                MDTextField:
                    id: entrada_titulo
                    hint_text: "Escreva a tarefa…"
                    mode: "fill"
                    fill_color: 1, 1, 1, 1
                    multiline: False
                MDIconButton:
                    icon: "plus"
                    on_release: app.adicionar()

            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(52)
                spacing: dp(8)
                padding: dp(4)

                MDTextField:
                    id: entrada_data
                    hint_text: "dd/mm/aaaa"
                    mode: "fill"
                    fill_color: 1, 1, 1, 1
                    multiline: False
                    size_hint_x: 0.45
                MDTextField:
                    id: entrada_categoria
                    hint_text: "Categoria"
                    text: "Pessoal"
                    mode: "fill"
                    fill_color: 1, 1, 1, 1
                    multiline: False
                    size_hint_x: 0.3
                MDTextField:
                    id: entrada_prio
                    hint_text: "Prioridade"
                    text: "Média"
                    mode: "fill"
                    fill_color: 1, 1, 1, 1
                    multiline: False
                    size_hint_x: 0.25

            MDLabel:
                id: lbl_progresso
                text: ""
                theme_text_color: "Custom"
                text_color: app.soft_text
                size_hint_y: None
                height: dp(22)
                font_style: "Caption"

            MDTextField:
                id: entrada_busca
                hint_text: "Buscar…"
                mode: "fill"
                fill_color: 1, 1, 1, 1
                multiline: False
                on_text: app.atualizar()

            MDBoxLayout:
                orientation: "horizontal"
                size_hint_y: None
                height: dp(48)
                spacing: dp(6)
                padding: dp(4)

                MDRaisedButton:
                    id: btn_status
                    text: "Status: Todas"
                    size_hint_x: 0.34
                    on_release: app.menu_status()
                MDRaisedButton:
                    id: btn_cat
                    text: "Cat: Todas"
                    size_hint_x: 0.4
                    on_release: app.menu_categoria()
                MDRaisedButton:
                    id: btn_limpar
                    text: "Limpar feitas"
                    size_hint_x: 0.26
                    on_release: app.limpar_feitas()

            ScrollView:
                MDList:
                    id: lista_tarefas

            MDLabel:
                id: lbl_count
                text: ""
                theme_text_color: "Custom"
                text_color: app.soft_text
                size_hint_y: None
                height: dp(22)
                font_style: "Caption"

<TextoScreen>:
    name: "texto"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "🖨 Texto livre"
            md_bg_color: app.titlebar
            specific_text_color: app.text_color

        MDBoxLayout:
            orientation: "vertical"
            padding: dp(8)
            spacing: dp(6)

            ScrollView:
                MDTextField:
                    id: txt_livre
                    hint_text: "Escreva aqui o texto livre…"
                    mode: "fill"
                    fill_color: 1, 1, 1, 1
                    multiline: True
                    size_hint_y: None
                    height: dp(400)

            MDLabel:
                id: lbl_aviso
                text: "A impressão SC03 no celular chega num próximo passo (Bluetooth)."
                theme_text_color: "Custom"
                text_color: app.soft_text
                size_hint_y: None
                height: dp(40)
                font_style: "Caption"
"""


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


class TarefasScreen(Screen):
    pass


class TextoScreen(Screen):
    pass


class ItemTarefa(TwoLineAvatarListItem):
    """Um item da lista com checkbox de concluir e botão de excluir."""

    def __init__(self, app, tarefa, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.tarefa = tarefa
        self.ids._txt_right.text = ""
        self.update_texto()
        self.cb = MDCheckbox(
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            active=bool(tarefa.get("concluida")),
            on_active=lambda cb, v: app.alternar(self, v),
        )
        self.add_widget(self.cb, index=1)
        self.add_widget(IconRightWidget(icon="pencil", on_release=lambda *a: app.editar(self)))
        self.add_widget(IconRightWidget(icon="delete", on_release=lambda *a: app.excluir(self)))

    def update_texto(self):
        t = self.tarefa
        self.text = t.get("titulo", "")
        prazostr = self._prazo()
        self.secondary_text = "%s · %s · %s" % (
            (t.get("categoria") or "—"),
            data_exibir(t.get("data", "")),
            prazostr,
        )

    def _prazo(self):
        t = self.tarefa
        if t.get("concluida"):
            return "Concluída"
        dias = dias_ate(t.get("data") or "")
        if t.get("data"):
            if dias is not None and dias < 0:
                return "● Atrasada %d d" % abs(dias)
            if dias == 0:
                return "● Vence hoje"
            if dias <= 2:
                return "Faltam %d d" % dias
            return "sem prazo"
        return "sem prazo"


class TarefasMobileApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Tarefas Diárias"
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.primary_hue = "100"
        self.theme_cls.theme_style = "Light"
        self.titlebar = TITLEBAR
        self.text_color = "#6E4A54"
        self.soft_text = TEXT_SOFT
        self.tarefas = []
        self.filtro = "Todas"
        self.status_filtro = "Todas"
        self.cat_filtro = "Todas"
        self.categorias_padrao = CATEGORIAS_PADRAO
        self._store = None
        self._arq = None
        self.dialog = None
        self._menu = None

    # ---------- arquivo ----------
    @property
    def arq(self):
        if self._arq is None:
            self._arq = os.path.join(self.user_data_dir, "tarefas.json")
        return self._arq

    def _carregar(self):
        if os.path.exists(self.arq):
            try:
                with open(self.arq, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.tarefas = dados.get("tarefas", []) if isinstance(dados, dict) else dados
            except Exception:
                self.tarefas = []
        if not isinstance(self.tarefas, list):
            self.tarefas = []

    def _salvar(self):
        try:
            with open(self.arq, "w", encoding="utf-8") as f:
                json.dump({"tarefas": self.tarefas}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._msg("Erro ao salvar", str(e))

    def _proximo_id(self):
        usados = {t["id"] for t in self.tarefas if isinstance(t.get("id"), str)}
        n = 1
        while str(n) in usados:
            n += 1
        return str(n)

    # ---------- telas ----------
    def build(self):
        self.root = Builder.load_string(KV)
        self._carregar()
        self.atualizar()
        return self.root

    # ---------- operações ----------
    def adicionar(self, *_):
        scr = self.root.get_screen("tarefas")
        titulo = (scr.ids.entrada_titulo.text or "").strip()
        if not titulo:
            self._msg("Tarefa", "Escreva o título da tarefa.")
            return
        data = scr.ids.entrada_data.text.strip()
        d_iso = self._ler_data(data)
        if d_iso is None:
            return
        categoria = (scr.ids.entrada_categoria.text or "Pessoal").strip() or "Pessoal"
        prio = (scr.ids.entrada_prio.text or "Média").strip() or "Média"
        self.tarefas.append({
            "id": self._proximo_id(),
            "titulo": titulo,
            "categoria": categoria,
            "data": d_iso,
            "prioridade": prio.lower(),
            "concluida": False,
            "criada_em": datetime.datetime.now().isoformat(timespec="seconds"),
            "concluida_em": "",
        })
        scr.ids.entrada_titulo.text = ""
        scr.ids.entrada_data.text = ""
        self._salvar()
        self.atualizar()

    def _ler_data(self, texto):
        texto = (texto or "").strip()
        if not texto:
            return ""
        try:
            return datetime.datetime.strptime(texto, "%d/%m/%Y").date().isoformat()
        except ValueError:
            self._msg("Data inválida", "Use o formato dd/mm/aaaa, ex: 25/12/2026.")
            return None

    def _filtradas(self):
        scr = self.root.get_screen("tarefas")
        b = (scr.ids.entrada_busca.text or "").strip().lower()
        cat = self.cat_filtro
        saida = []
        for t in self.tarefas:
            if self.status_filtro == "Pendentes" and t.get("concluida"):
                continue
            if self.status_filtro == "Concluídas" and not t.get("concluida"):
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

    def _linhas_atuais(self):
        def chave(t):
            pr = {"alta": 0, "media": 1, "baixa": 2}.get((t.get("prioridade") or "media").lower(), 1)
            d = t.get("data") or "9999-99-99"
            cat = (t.get("categoria") or "").strip().upper() or "zzz"
            concluida = 1 if t.get("concluida") else 0
            concluida_em = t.get("concluida_em") or ""
            return (concluida, cat, d, pr, concluida_em)
        return sorted(self._filtradas(), key=chave)

    def atualizar(self):
        scr = self.root.get_screen("tarefas")
        lista = scr.ids.lista_tarefas
        lista.clear_widgets()
        pendentes = [t for t in self.tarefas if not t.get("concluida")]
        feitas = len(self.tarefas) - len(pendentes)
        for t in self._linhas_atuais():
            lista.add_widget(ItemTarefa(self, t))
        scr.ids.lbl_progresso.text = "✿ %d pendente(s) · %d concluída(s)" % (len(pendentes), feitas)
        scr.ids.lbl_count.text = "Total: %d tarefa(s) · %d pendente(s) · %d concluída(s)" % (
            len(self.tarefas), len(pendentes), feitas)

    def alternar(self, item, valor):
        item.tarefa["concluida"] = bool(valor)
        item.tarefa["concluida_em"] = datetime.datetime.now().isoformat(
            timespec="seconds") if valor else ""
        self._salvar()
        self.atualizar()

    def excluir(self, item):
        t = item.tarefa
        self._confirmar(
            "Excluir tarefa",
            "Excluir a tarefa:\n  “%s”?" % t.get("titulo", ""),
            lambda: self._excluir_ok(t),
        )

    def _excluir_ok(self, t):
        self.tarefas = [x for x in self.tarefas if x.get("id") != t.get("id")]
        self._salvar()
        self.atualizar()

    def menu_status(self, *_):
        opcoes = ["Todas", "Pendentes", "Concluídas"]
        items = [{"text": o, "viewclass": "OneLineListItem",
                  "on_release": lambda o=o: self._set_filtro_status(o)}
                 for o in opcoes]
        self._abrir_menu(items, self.root.get_screen("tarefas").ids.btn_status)

    def _set_filtro_status(self, o):
        self._fechar_menu()
        self.status_filtro = o
        self.root.get_screen("tarefas").ids.btn_status.text = "Status: %s" % o
        self.atualizar()

    def menu_categoria(self, *_):
        cats = ["Todas"] + self._categorias_em_uso()
        items = [{"text": c, "viewclass": "OneLineListItem",
                  "on_release": lambda c=c: self._set_filtro_cat(c)}
                 for c in cats]
        self._abrir_menu(items, self.root.get_screen("tarefas").ids.btn_cat)

    def _set_filtro_cat(self, c):
        self._fechar_menu()
        self.cat_filtro = c
        self.root.get_screen("tarefas").ids.btn_cat.text = "Cat: %s" % c
        self.atualizar()

    def _abrir_menu(self, items, caller):
        self._fechar_menu()
        try:
            self._menu = MDDropdownMenu(caller=caller, items=items, width_mult=4)
        except TypeError:
            self._menu = MDDropdownMenu(caller=caller, items=items)
        self._menu.open()

    def _fechar_menu(self):
        if getattr(self, "_menu", None) is not None:
            try:
                self._menu.dismiss()
            except Exception:
                pass
            self._menu = None

    def limpar_feitas(self, *_):
        feitas = [t for t in self.tarefas if t.get("concluida")]
        if not feitas:
            self._msg("Limpar concluídas", "Nenhuma tarefa concluída.")
            return
        self._confirmar(
            "Limpar concluídas",
            "Remover %d tarefa(s) já concluída(s)?" % len(feitas),
            lambda: self._limpar_ok(feitas),
        )

    def _limpar_ok(self, feitas):
        ids = {t.get("id") for t in feitas}
        self.tarefas = [t for t in self.tarefas if t.get("id") not in ids]
        self._salvar()
        self.atualizar()

    def editar(self, item):
        t = item.tarefa
        scr = self.root.get_screen("tarefas")
        scr.ids.entrada_titulo.text = t.get("titulo", "")
        scr.ids.entrada_data.text = data_exibir(t.get("data", "")) if t.get("data") else ""
        scr.ids.entrada_categoria.text = t.get("categoria", "") or ""
        scr.ids.entrada_prio.text = (t.get("prioridade") or "media").capitalize()
        self._msg("Editar", "Ajuste os campos acima e toque em ＋ Adicionar.\n"
                            "Para alterar a tarefa existente, toque em Salvar.")
        self._confirmar("Salvar edição", "Aplicar as mudanças em “%s”?" % t.get("titulo", ""),
                        lambda: self._editar_ok(t, scr))

    def _editar_ok(self, t, scr):
        titulo = (scr.ids.entrada_titulo.text or "").strip()
        if not titulo:
            self._msg("Editar", "O título não pode ficar vazio.")
            return
        d_iso = self._ler_data(scr.ids.entrada_data.text.strip())
        if d_iso is None:
            return
        t["titulo"] = titulo
        t["data"] = d_iso
        t["categoria"] = (scr.ids.entrada_categoria.text or "").strip()
        t["prioridade"] = (scr.ids.entrada_prio.text or "Média").lower()
        self._salvar()
        self.atualizar()

    def exportar(self, *_):
        try:
            from plyer import filechooser
        except Exception:
            self._msg("Exportar", "Filechooser indisponível neste dispositivo.")
            return
        caminho = os.path.join(self.user_data_dir,
                               "tarefas_diarias_%s.json" % datetime.date.today().isoformat())
        try:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump({"tarefas": self.tarefas}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._msg("Erro ao exportar", str(e))
            return
        self._confirmar("Exportar", "Arquivo criado:\n%s\n\nQuer salvar uma cópia em outro lugar?"
                                     % caminho,
                        lambda: filechooser.save_file(
                            on_selection=lambda paths: self._copiar_export(paths, caminho)))

    def _copiar_export(self, paths, origem):
        if paths and os.path.exists(origem):
            try:
                with open(origem, "r", encoding="utf-8") as src:
                    dados = src.read()
                with open(paths[0], "w", encoding="utf-8") as dst:
                    dst.write(dados)
                self._msg("Exportar", "Tarefas exportadas com sucesso.")
            except Exception as e:
                self._msg("Erro ao exportar", str(e))

    def importar(self, *_):
        try:
            from plyer import filechooser
        except Exception:
            self._msg("Importar", "Filechooser indisponível neste dispositivo.")
            return
        filechooser.open_file(
            filters=["*.json"],
            on_selection=lambda paths: self._importar_ok(paths),
        )

    def _importar_ok(self, paths):
        if not paths:
            return
        try:
            with open(paths[0], "r", encoding="utf-8") as f:
                dados = json.load(f)
            novos = dados.get("tarefas", []) if isinstance(dados, dict) else dados
            if not isinstance(novos, list):
                raise ValueError("arquivo sem a lista de tarefas")
        except Exception as e:
            self._msg("Importar", "Não dá pra ler esse arquivo:\n%s" % e)
            return
        for t in novos:
            t.setdefault("concluida", False)
            t.setdefault("prioridade", "media")
            t.setdefault("data", "")
            t.setdefault("categoria", "")
        self.tarefas = novos
        self._salvar()
        self.atualizar()
        self._msg("Importar", "Pronto! %d tarefa(s) importada(s)." % len(novos))

    # ---------- diálogos ----------
    def _confirmar(self, titulo, texto, ao_ok):
        self.dialog = MDDialog(
            title=titulo,
            text=texto,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda *a: self.dialog.dismiss()),
                MDRaisedButton(text="OK", on_release=lambda *a: (self.dialog.dismiss(), ao_ok())),
            ],
        )
        self.dialog.open()

    def _msg(self, titulo, texto):
        self.dialog = MDDialog(title=titulo, text=texto, buttons=[
            MDFlatButton(text="OK", on_release=lambda *a: self.dialog.dismiss()),
        ])
        self.dialog.open()


if __name__ == "__main__":
    TarefasMobileApp().run()