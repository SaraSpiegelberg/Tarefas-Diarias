# -*- mode: python ; coding: utf-8 -*-
# buildozer.spec — Tarefas Diárias ✿ (KivyMD)
#
# Build (em Linux/WSL):
#     buildozer android debug
#
# O ícone vem de ../assets/app.png (mesmo do desktop).
# Permissões mínimas: o importar/exportar usa o seletor de arquivos do Android
# (SAF) e não precisa de permissão de armazenamento.
# A impressão SC03 via Bluetooth será um passo futuro -> aí entram as permissões
# BLUETOOTH/BLUETOOTH_CONNECT.

[app]
title = Tarefas Diárias
package.name = tarefasdiarias
package.domain = org.sara

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.1.0

requirements = python3,kivymd,plyer

orientation = portrait
fullscreen = 0

# ícone do app (dentro do source.dir — obrigatório para o buildozer)
icon.filename = assets/icon.png

# presplash (tela de carregamento) — opcional
#presplash.filename = assets/icon.png

# Permissões: nenhuma obrigatória por enquanto (o app NÃO usa internet).
# O importar/exportar usa o seletor de arquivos do Android (SAF) e não pede
# permissão de armazenamento.
# A impressão SC03 via Bluetooth será um passo futuro -> aí entram as permissões
# BLUETOOTH/BLUETOOTH_CONNECT.
android.permissions =
android.accept_sdk_license = True
android.api = 33
android.minapi = 21

android.allow_backup = True
android.private_storage = True

android.archs = arm64-v8a

# --- opções de build ---
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1