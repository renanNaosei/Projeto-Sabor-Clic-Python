import secrets

from flask import flash, jsonify, request, session

from app.extensions import db
from app.models import Cliente, Usuario
from app.security import (
    limpar_falhas_login,
    login_bloqueado,
    registrar_falha_login,
    resposta_erro,
    usuario_atual,
)
from app.services.erros import confirmar
from app.services.validacao_service import validar_cadastro


def obter_token_csrf():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return jsonify({"sucesso": True, "csrf_token": token})


def registrar_cliente():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return resposta_erro("O corpo deve ser JSON.", 400, "JSON_INVALIDO")

    erros = validar_cadastro(dados)
    if erros:
        return resposta_erro("Não foi possível validar o cadastro.", 400, "VALIDACAO", erros)

    email = dados["email"].strip().lower()
    if Usuario.query.filter_by(email=email).first():
        return resposta_erro("Este e-mail já está cadastrado.", 409, "EMAIL_EXISTENTE")

    # O papel nunca vem do cliente: o cadastro público sempre cria 'cliente'.
    usuario = Usuario(
        nome=dados["nome"].strip(),
        email=email,
        tipo_usuario="cliente",
        cliente=Cliente(
            telefone=(dados.get("telefone") or "").strip() or None,
            endereco_entrega=(dados.get("endereco_entrega") or "").strip() or None,
        ),
    )
    usuario.definir_senha(dados["senha"])
    db.session.add(usuario)
    confirmar()

    flash("Cadastro realizado. Entre com seu e-mail e senha.", "sucesso")
    return jsonify(
        {
            "sucesso": True,
            "mensagem": "Cadastro realizado. Entre com seu e-mail e senha.",
            "dados": usuario.to_dict(),
        }
    ), 201


def entrar():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return resposta_erro("O corpo deve ser JSON.", 400, "JSON_INVALIDO")

    email, senha = dados.get("email"), dados.get("senha")
    if not isinstance(email, str) or not isinstance(senha, str) or len(senha) > 256:
        return resposta_erro("E-mail e senha são obrigatórios.", 400, "VALIDACAO")

    if login_bloqueado(email):
        return resposta_erro(
            "Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
            429,
            "TENTATIVAS_EXCESSIVAS",
        )

    usuario = Usuario.query.filter_by(email=email.strip().lower()).first()
    # Mensagem genérica: não revela se o e-mail existe.
    if usuario is None or not usuario.ativo or not usuario.conferir_senha(senha):
        registrar_falha_login(email)
        return resposta_erro("E-mail ou senha inválidos.", 401, "CREDENCIAIS_INVALIDAS")

    limpar_falhas_login(email)
    # Limpa a sessão anterior (evita session fixation) e gera novo token CSRF.
    session.clear()
    session.permanent = True
    session["usuario_id"] = usuario.id_usuario
    session["csrf_token"] = secrets.token_urlsafe(32)
    flash(f"Bem-vindo(a), {usuario.nome}!", "sucesso")

    return jsonify(
        {
            "sucesso": True,
            "mensagem": "Login realizado com sucesso.",
            "dados": usuario.to_dict(),
            "csrf_token": session["csrf_token"],
        }
    )


def sair():
    session.clear()
    return jsonify({"sucesso": True, "mensagem": "Sessão encerrada."})


def perfil_atual():
    usuario = usuario_atual()
    if usuario is None:
        return jsonify({"sucesso": True, "autenticado": False, "dados": None})
    return jsonify({"sucesso": True, "autenticado": True, "dados": usuario.to_dict()})
