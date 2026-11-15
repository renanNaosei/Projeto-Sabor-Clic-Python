import os
import secrets
from datetime import timedelta

# SQLite: um arquivo só, criado em backend/instance/ (não precisa instalar servidor nem driver).
DATABASE_PADRAO = "sqlite:///sabor_clic.db"


def _booleano(nome, padrao="false"):
    return os.getenv(nome, padrao).strip().lower() == "true"


class Config:
    """Configuração padrão: SQLite local. Tudo pode ser trocado por variável de ambiente."""

    # Sem SECRET_KEY no ambiente, usa uma chave aleatória (nunca um valor fixo conhecido).
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SECRET_KEY_ALEATORIA = not os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DATABASE_PADRAO)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_NAME = "saborclic_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _booleano("SESSION_COOKIE_SECURE")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    MAX_CONTENT_LENGTH = 1 * 1024 * 1024

    # Limite de tentativas de login erradas por (IP + e-mail) dentro da janela.
    LOGIN_MAX_FALHAS = 5
    LOGIN_JANELA_SEGUNDOS = 300

    # Nunca use '*' com supports_credentials=True. Informe apenas origens confiáveis.
    CORS_ORIGINS = tuple(
        origem.strip()
        for origem in os.getenv(
            "CORS_ORIGINS", "http://127.0.0.1:5500,http://127.0.0.1:5000"
        ).split(",")
        if origem.strip()
    )
