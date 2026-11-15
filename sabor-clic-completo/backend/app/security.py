"""Autenticação, autorização (RBAC) e proteção contra força bruta no login."""
import threading
import time
from functools import wraps

from flask import current_app, jsonify, request, session

from app.extensions import db
from app.models import Usuario


def resposta_erro(mensagem, status, codigo=None, detalhes=None):
    corpo = {"sucesso": False, "erro": mensagem}
    if codigo:
        corpo["codigo"] = codigo
    if detalhes:
        corpo["detalhes"] = detalhes
    return jsonify(corpo), status


def usuario_atual():
    """Obtém o usuário no banco; o cookie guarda apenas o identificador.

    O cache fica no objeto `request` (um novo por requisição) e não em `g`:
    `g` pertence ao contexto da aplicação, que nos testes é um só para várias
    requisições, e o usuário de uma requisição "vazava" para a seguinte.
    """
    if hasattr(request, "_usuario_atual"):
        return request._usuario_atual

    usuario_id = session.get("usuario_id")
    if not usuario_id:
        request._usuario_atual = None
        return None

    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        session.clear()
        request._usuario_atual = None
        return None

    request._usuario_atual = usuario
    return usuario


def login_obrigatorio(funcao):
    @wraps(funcao)
    def wrapper(*args, **kwargs):
        if usuario_atual() is None:
            return resposta_erro("Autenticação necessária.", 401, "NAO_AUTENTICADO")
        return funcao(*args, **kwargs)

    return wrapper


def papeis_obrigatorios(*papeis):
    """RBAC: 401 se não autenticado; 403 se o perfil não é um dos permitidos."""
    permitidos = set(papeis)

    def decorator(funcao):
        @wraps(funcao)
        def wrapper(*args, **kwargs):
            usuario = usuario_atual()
            if usuario is None:
                return resposta_erro("Autenticação necessária.", 401, "NAO_AUTENTICADO")
            if usuario.tipo_usuario not in permitidos:
                return resposta_erro(
                    "Seu perfil não possui permissão para esta operação.",
                    403,
                    "ACESSO_NEGADO",
                )
            return funcao(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Limitação de tentativas de login (em memória: suficiente para um servidor só)
# ---------------------------------------------------------------------------
_falhas = {}
_trava = threading.Lock()


def _chave_login(email):
    return f"{request.remote_addr}|{(email or '').strip().lower()}"


def _falhas_recentes(chave, agora):
    janela = current_app.config["LOGIN_JANELA_SEGUNDOS"]
    recentes = [t for t in _falhas.get(chave, []) if agora - t < janela]
    if recentes:
        _falhas[chave] = recentes
    else:
        _falhas.pop(chave, None)
    return recentes


def login_bloqueado(email):
    with _trava:
        recentes = _falhas_recentes(_chave_login(email), time.monotonic())
        return len(recentes) >= current_app.config["LOGIN_MAX_FALHAS"]


def registrar_falha_login(email):
    with _trava:
        agora = time.monotonic()
        chave = _chave_login(email)
        recentes = _falhas_recentes(chave, agora)
        recentes.append(agora)
        _falhas[chave] = recentes


def limpar_falhas_login(email):
    with _trava:
        _falhas.pop(_chave_login(email), None)


def zerar_tentativas():
    """Uso em testes."""
    with _trava:
        _falhas.clear()