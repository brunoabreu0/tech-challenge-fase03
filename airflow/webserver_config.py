# ==============================================================================
# webserver_config.py — Configuração do Airflow Webserver (Flask-AppBuilder)
# Permite acesso anônimo somente-leitura (Viewer) para banca e avaliadores.
# ==============================================================================

from __future__ import annotations

import os

from flask_appbuilder.const import AUTH_DB

basedir = os.path.abspath(os.path.dirname(__file__))

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# ----------------------------------------------------
# AUTHENTICATION CONFIG
# ----------------------------------------------------
AUTH_TYPE = AUTH_DB

# Permite acesso direto sem tela de login com perfil somente-leitura (Viewer)
AUTH_ROLE_PUBLIC = "Viewer"

# Não permite auto-registro
AUTH_USER_REGISTRATION = False
