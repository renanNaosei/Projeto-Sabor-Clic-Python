import hmac
import os

import click
from flask import Flask, request, session
from flask_cors import CORS
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.extensions import db
from app.security import resposta_erro, usuario_atual
from app.services.erros import ErroDeNegocio, traduzir_erro_do_banco

METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if app.config.get("SECRET_KEY_ALEATORIA") and not app.testing:
        app.logger.warning(
            "SECRET_KEY não definida: usando chave aleatória. As sessões serão "
            "invalidadas a cada reinício. Defina SECRET_KEY no arquivo .env."
        )

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    origens = app.config.get("CORS_ORIGINS", ())
    if origens:
        CORS(
            app,
            resources={r"/api/*": {"origins": list(origens)}},
            supports_credentials=True,
            allow_headers=["Content-Type", "X-CSRF-Token"],
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        )

    @app.before_request
    def carregar_usuario_e_validar_csrf():
        usuario_atual()
        if request.path.startswith("/api/") and request.method not in METODOS_SEGUROS:
            token_sessao = session.get("csrf_token")
            token_requisicao = request.headers.get("X-CSRF-Token", "")
            if (
                not token_sessao
                or not token_requisicao
                or not hmac.compare_digest(token_sessao, token_requisicao)
            ):
                return resposta_erro(
                    "Token CSRF ausente ou inválido. Atualize o token e tente novamente.",
                    403,
                    "CSRF_INVALIDO",
                )

    @app.after_request
    def cabecalhos_de_seguranca(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.path.startswith("/api/"):
            resposta.headers.setdefault("Cache-Control", "no-store")
        return resposta

    from app.routes.agendamento_routes import agendamento_bp, bancada_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.estoque_routes import estoque_bp
    from app.routes.health_routes import health_bp
    from app.routes.menu_routes import menu_bp
    from app.routes.mensagens_routes import mensagens_bp
    from app.routes.pedido_routes import pedido_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(menu_bp, url_prefix="/api/menu")
    app.register_blueprint(pedido_bp, url_prefix="/api/pedidos")
    app.register_blueprint(estoque_bp, url_prefix="/api/estoque")
    app.register_blueprint(bancada_bp, url_prefix="/api/bancadas")
    app.register_blueprint(agendamento_bp, url_prefix="/api/agendamentos")
    app.register_blueprint(mensagens_bp, url_prefix="/api/mensagens")

    # ----------------------------- tratamento de erros -----------------------------
    @app.errorhandler(ErroDeNegocio)
    def erro_de_negocio(erro):
        return resposta_erro(erro.mensagem, erro.status, erro.codigo, erro.detalhes)

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return resposta_erro("Rota ou recurso não encontrado.", 404, "NAO_ENCONTRADO")

    @app.errorhandler(405)
    def metodo_nao_permitido(_erro):
        return resposta_erro("Método HTTP não permitido.", 405, "METODO_NAO_PERMITIDO")

    @app.errorhandler(IntegrityError)
    def erro_de_integridade(erro):
        db.session.rollback()
        traduzido = traduzir_erro_do_banco(erro)
        if traduzido:
            return erro_de_negocio(traduzido)
        return resposta_erro(
            "A operação viola uma regra de integridade da base de dados.", 409, "CONFLITO_BD"
        )

    @app.errorhandler(SQLAlchemyError)
    def erro_de_banco(erro):
        db.session.rollback()
        if isinstance(erro, DBAPIError):
            traduzido = traduzir_erro_do_banco(erro)
            if traduzido:
                return erro_de_negocio(traduzido)
        app.logger.exception("Falha na operação com o banco de dados: %s", erro)
        return resposta_erro(
            "Não foi possível concluir a operação no banco de dados.", 500, "ERRO_BD"
        )

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        return resposta_erro(erro.description, erro.code or 500, "ERRO_HTTP")

    @app.errorhandler(Exception)
    def erro_inesperado(erro):
        app.logger.exception("Erro inesperado: %s", erro)
        return resposta_erro("Ocorreu um erro interno. Tente novamente.", 500, "ERRO_INTERNO")

    # ------------------------------- comandos CLI ---------------------------------
    @app.cli.command("init-db")
    @click.option("--sem-dados", is_flag=True, help="Cria só as tabelas e triggers, sem os dados de exemplo.")
    @click.option("--sim", is_flag=True, help="Não pedir confirmação se o banco já tiver dados.")
    def init_db(sem_dados, sim):
        """Recria o banco SQLite executando os scripts de database/ (APAGA os dados atuais)."""
        from app.banco import banco_tem_dados, criar_banco

        if banco_tem_dados() and not sim:
            click.confirm("O banco já tem dados e eles serão apagados. Continuar?", abort=True)
        scripts = criar_banco(com_dados=not sem_dados)
        click.echo("Banco criado com: " + ", ".join(scripts))
        if not sem_dados:
            click.echo("Usuários de teste (senha Senha@123): ana.admin@, bruno.cliente@, carla.cozinha@ ... saborclic.com")

    @app.cli.command("criar-usuario")
    @click.option("--nome", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    @click.option(
        "--papel",
        type=click.Choice(["administrador", "cozinheiro"]),
        prompt="Papel",
    )
    @click.option(
        "--turno",
        type=click.Choice(["Manhã", "Tarde", "Noite"]),
        default="Manhã",
        show_default=True,
        help="Turno (apenas para cozinheiro).",
    )
    @click.option("--senha", prompt=True, hide_input=True, confirmation_prompt=True)
    def criar_usuario(nome, email, papel, turno, senha):
        """Cria administrador/cozinheiro (não existe cadastro privilegiado na API)."""
        from app.models import Administrador, Cozinheiro, Usuario

        email = email.strip().lower()
        if Usuario.query.filter_by(email=email).first():
            raise click.ClickException("Já existe usuário com esse e-mail.")
        if len(senha) < 8:
            raise click.ClickException("A senha deve ter pelo menos 8 caracteres.")

        usuario = Usuario(nome=nome.strip(), email=email, tipo_usuario=papel)
        usuario.definir_senha(senha)
        if papel == "administrador":
            usuario.administrador = Administrador(nivel_permissao="TOTAL")
        else:
            usuario.cozinheiro = Cozinheiro(turno_trabalho=turno)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuário '{papel}' criado com ID {usuario.id_usuario}.")

    return app
