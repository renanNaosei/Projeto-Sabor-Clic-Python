import pytest

from app import create_app
from app.banco import criar_banco
from app.extensions import db
from app.security import zerar_tentativas


@pytest.fixture
def app():
    zerar_tentativas()
    aplicacao = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-de-teste-nao-usar-em-producao",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SESSION_COOKIE_SECURE": False,
            "CORS_ORIGINS": ("http://127.0.0.1:5500",),
        }
    )
    with aplicacao.app_context():
        # Mesmo schema e triggers de database/ (sem os dados de exemplo): os testes exercitam os triggers de verdade.
        criar_banco(com_dados=False)
        yield aplicacao
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()
