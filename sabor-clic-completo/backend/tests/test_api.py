from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError

from app.banco import criar_banco
from app.extensions import db
from app.models import (
    Administrador,
    Agendamento,
    Bancada,
    Cliente,
    Cozinheiro,
    FichaTecnica,
    Ingrediente,
    ItemPedido,
    Pedido,
    Prato,
    Usuario,
)
from app.services.erros import traduzir_erro_do_banco

SENHA = "SenhaSegura123"


# ----------------------------- auxiliares -----------------------------
def token_csrf(client):
    resposta = client.get("/api/auth/csrf")
    assert resposta.status_code == 200
    return resposta.get_json()["csrf_token"]


def cadastrar_cliente(client, email="cliente@example.com"):
    resposta = client.post(
        "/api/auth/register",
        json={"nome": "Cliente Teste", "email": email, "senha": SENHA},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert resposta.status_code == 201
    return resposta.get_json()["dados"]


def criar_usuario_papel(app, papel, email):
    with app.app_context():
        usuario = Usuario(nome=f"{papel} Teste", email=email, tipo_usuario=papel)
        usuario.definir_senha(SENHA)
        if papel == "administrador":
            usuario.administrador = Administrador(nivel_permissao="TOTAL")
        elif papel == "cozinheiro":
            usuario.cozinheiro = Cozinheiro(turno_trabalho="Manhã")
        else:
            usuario.cliente = Cliente()
        db.session.add(usuario)
        db.session.commit()
        return usuario.id_usuario


def login(client, email, senha=SENHA, esperado=200):
    resposta = client.post(
        "/api/auth/login",
        json={"email": email, "senha": senha},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert resposta.status_code == esperado
    return resposta.get_json().get("csrf_token")


def novo_prato(client, token, **extra):
    corpo = {
        "nome": "Hambúrguer artesanal",
        "descricao": "Pão, carne e queijo",
        "preco": "25.90",
        "categoria": "Lanches",
    }
    corpo.update(extra)
    resposta = client.post("/api/menu", json=corpo, headers={"X-CSRF-Token": token})
    assert resposta.status_code == 201
    return resposta.get_json()["dados"]["id"]


def prato_como_admin(app, client):
    criar_usuario_papel(app, "administrador", "admin@example.com")
    token = login(client, "admin@example.com")
    prato_id = novo_prato(client, token)
    client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
    return prato_id


def pedido_como_cliente(app, client, quantidade=1):
    prato_id = prato_como_admin(app, client)
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    resposta = client.post(
        "/api/pedidos",
        json={"itens": [{"prato_id": prato_id, "quantidade": quantidade}]},
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 201
    return token, resposta.get_json()["dados"]["id"]


# ----------------------------- base e segurança -----------------------------
def test_health_e_cardapio_publico_vazio(client):
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/menu").get_json() == {"sucesso": True, "dados": []}


def test_cabecalhos_de_seguranca(client):
    resposta = client.get("/api/health")
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"


def test_csrf_exigido_nas_rotas_que_alteram_dados(client):
    resposta = client.post("/api/auth/register", json={})
    assert resposta.status_code == 403
    assert resposta.get_json()["codigo"] == "CSRF_INVALIDO"


def test_cadastro_publico_sempre_cria_cliente(client):
    resposta = client.post(
        "/api/auth/register",
        json={
            "nome": "Tentativa",
            "email": "tentativa@example.com",
            "senha": SENHA,
            "papel": "ADMINISTRADOR",
            "tipo_usuario": "administrador",
        },
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert resposta.status_code == 201
    dados = resposta.get_json()["dados"]
    assert dados["tipo_usuario"] == "cliente"
    assert dados["papel"] == "CLIENTE"


def test_cadastro_com_email_repetido_retorna_409(client):
    cadastrar_cliente(client)
    resposta = client.post(
        "/api/auth/register",
        json={"nome": "Outro", "email": "CLIENTE@example.com", "senha": SENHA},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert resposta.status_code == 409


def test_cadastro_com_dados_invalidos_retorna_400(client):
    resposta = client.post(
        "/api/auth/register",
        json={"nome": "", "email": "sem-arroba", "senha": "curta"},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert resposta.status_code == 400
    assert len(resposta.get_json()["detalhes"]) == 3


def test_login_invalido_e_generico(client):
    cadastrar_cliente(client)
    errado = client.post(
        "/api/auth/login",
        json={"email": "cliente@example.com", "senha": "errada-123"},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    inexistente = client.post(
        "/api/auth/login",
        json={"email": "ninguem@example.com", "senha": "errada-123"},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert errado.status_code == inexistente.status_code == 401
    assert errado.get_json()["erro"] == inexistente.get_json()["erro"]


def test_login_bloqueia_apos_varias_falhas(app, client):
    cadastrar_cliente(client)
    for _ in range(app.config["LOGIN_MAX_FALHAS"]):
        login(client, "cliente@example.com", senha="errada-123", esperado=401)
    resposta = client.post(
        "/api/auth/login",
        json={"email": "cliente@example.com", "senha": SENHA},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert resposta.status_code == 429
    assert resposta.get_json()["codigo"] == "TENTATIVAS_EXCESSIVAS"


def test_me_sem_login_retorna_dados_nulos(client):
    corpo = client.get("/api/auth/me").get_json()
    assert corpo["autenticado"] is False and corpo["dados"] is None


def test_logout_exige_login(client):
    resposta = client.post("/api/auth/logout", headers={"X-CSRF-Token": token_csrf(client)})
    assert resposta.status_code == 401


def test_mensagens_flash_sao_entregues_uma_vez(client):
    cadastrar_cliente(client)
    login(client, "cliente@example.com")
    primeira = client.get("/api/mensagens").get_json()["dados"]
    assert any("Bem-vindo" in m["texto"] for m in primeira)
    assert client.get("/api/mensagens").get_json()["dados"] == []


# ----------------------------- cardápio -----------------------------
def test_cliente_nao_cria_prato(app, client):
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    resposta = client.post(
        "/api/menu",
        json={"nome": "Prato", "descricao": "Teste", "preco": 10},
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 403
    assert resposta.get_json()["codigo"] == "ACESSO_NEGADO"


def test_admin_cria_edita_e_desativa_prato(app, client):
    criar_usuario_papel(app, "administrador", "admin@example.com")
    token = login(client, "admin@example.com")
    prato_id = novo_prato(client, token, imagem="https://exemplo.com/a.jpg")
    cabecalho = {"X-CSRF-Token": token}

    editado = client.patch(f"/api/menu/{prato_id}", json={"preco": "30.00"}, headers=cabecalho)
    assert editado.status_code == 200
    assert editado.get_json()["dados"]["preco"] == 30.0
    assert editado.get_json()["dados"]["imagem"] == "https://exemplo.com/a.jpg"

    assert client.delete(f"/api/menu/{prato_id}", headers=cabecalho).status_code == 200
    assert client.get("/api/menu").get_json()["dados"] == []
    assert len(client.get("/api/menu?ativo=false").get_json()["dados"]) == 1


def test_visitante_nao_ve_prato_desativado_nem_usa_ativo_false(app, client):
    criar_usuario_papel(app, "administrador", "admin@example.com")
    token = login(client, "admin@example.com")
    prato_id = novo_prato(client, token, disponivel=False)
    client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
    assert client.get(f"/api/menu/{prato_id}").status_code == 404
    assert client.get("/api/menu?ativo=false").get_json()["dados"] == []


def test_prato_rejeita_campos_e_precos_invalidos(app, client):
    criar_usuario_papel(app, "administrador", "admin@example.com")
    token = login(client, "admin@example.com")
    for corpo in (
        {"nome": "X", "descricao": "d", "preco": "abc"},
        {"nome": "X", "descricao": "d", "preco": -1},
        {"nome": "X", "descricao": "d", "preco": "1.234"},
        {"nome": "X", "descricao": "d", "preco": 1, "admin": True},
        {"nome": "X", "descricao": "d", "preco": 1, "imagem": "javascript:alert(1)"},
    ):
        resposta = client.post("/api/menu", json=corpo, headers={"X-CSRF-Token": token})
        assert resposta.status_code == 400, corpo


def test_texto_com_sql_injection_e_gravado_como_dado(app, client):
    criar_usuario_papel(app, "administrador", "admin@example.com")
    token = login(client, "admin@example.com")
    texto = "' OR 1=1 --"
    novo_prato(client, token, nome=texto)
    assert [p["nome"] for p in client.get("/api/menu").get_json()["dados"]] == [texto]


# ----------------------------- pedidos -----------------------------
def test_pedido_usa_preco_do_banco_e_cliente_da_sessao(app, client):
    prato_id = prato_como_admin(app, client)
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    resposta = client.post(
        "/api/pedidos",
        json={
            "itens": [{"prato_id": prato_id, "quantidade": 2, "preco": 0.01}],
            "observacoes": "  sem   cebola ",
        },
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 201
    pedido = resposta.get_json()["dados"]
    assert Decimal(pedido["valor_total"]) == Decimal("51.80")
    assert Decimal(pedido["itens"][0]["preco_unitario"]) == Decimal("25.90")
    assert pedido["itens"][0]["nome"] == "Hambúrguer artesanal"
    assert pedido["observacoes"] == "sem cebola"
    assert pedido["status"] == "Aguardando"


def test_pedido_soma_linhas_repetidas_do_mesmo_prato(app, client):
    prato_id = prato_como_admin(app, client)
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    resposta = client.post(
        "/api/pedidos",
        json={"itens": [{"prato_id": prato_id, "quantidade": 1}] * 3},
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 201
    assert len(resposta.get_json()["dados"]["itens"]) == 1
    assert resposta.get_json()["dados"]["itens"][0]["quantidade"] == 3


def test_pedido_invalido_retorna_400(app, client):
    prato_id = prato_como_admin(app, client)
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    for itens in (
        [],
        "x",
        [{"prato_id": prato_id, "quantidade": 0}],
        [{"prato_id": prato_id, "quantidade": 100}],
        [{"prato_id": True, "quantidade": 1}],
        [{"prato_id": prato_id, "quantidade": "2"}],
    ):
        resposta = client.post("/api/pedidos", json={"itens": itens}, headers={"X-CSRF-Token": token})
        assert resposta.status_code == 400, itens


def test_pedido_com_prato_inexistente_retorna_409(app, client):
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    resposta = client.post(
        "/api/pedidos",
        json={"itens": [{"prato_id": 999, "quantidade": 1}]},
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 409
    assert resposta.get_json()["codigo"] == "PRATOS_INDISPONIVEIS"


def test_cliente_nao_cria_pedido_em_nome_de_outro(app, client):
    prato_id = prato_como_admin(app, client)
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    resposta = client.post(
        "/api/pedidos",
        json={"cliente_id": 999999, "itens": [{"prato_id": prato_id, "quantidade": 1}]},
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 403
    assert resposta.get_json()["codigo"] == "CLIENTE_DIVERGENTE"


def test_visitante_nao_cria_pedido(client):
    resposta = client.post(
        "/api/pedidos",
        json={"itens": [{"prato_id": 1, "quantidade": 1}]},
        headers={"X-CSRF-Token": token_csrf(client)},
    )
    assert resposta.status_code == 401


def test_cliente_nao_atualiza_status(app, client):
    token, pedido_id = pedido_como_cliente(app, client)
    resposta = client.patch(
        f"/api/pedidos/{pedido_id}/status",
        json={"status": "Iniciando Preparo"},
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 403


def test_cliente_nao_ve_pedido_de_outro_cliente(app, client):
    token, pedido_id = pedido_como_cliente(app, client)
    client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
    cadastrar_cliente(client, "outro@example.com")
    login(client, "outro@example.com")
    assert client.get(f"/api/pedidos/{pedido_id}").status_code == 404
    assert client.get("/api/pedidos/meus").get_json()["dados"] == []


def test_cliente_nao_lista_fila_da_cozinha(app, client):
    pedido_como_cliente(app, client)
    assert client.get("/api/pedidos").status_code == 403


def test_cozinheiro_percorre_estados_permitidos(app, client):
    token, pedido_id = pedido_como_cliente(app, client)
    client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
    criar_usuario_papel(app, "cozinheiro", "cozinha@example.com")
    cozinha = login(client, "cozinha@example.com")
    for status in ("Iniciando Preparo", "Em Preparo", "Pronto para Entrega"):
        resposta = client.patch(
            f"/api/pedidos/{pedido_id}/status", json={"status": status}, headers={"X-CSRF-Token": cozinha}
        )
        assert resposta.status_code == 200
        assert resposta.get_json()["dados"]["status"] == status
    assert len(client.get("/api/pedidos").get_json()["dados"]) == 1


def test_cozinheiro_nao_pula_nem_volta_status(app, client):
    token, pedido_id = pedido_como_cliente(app, client)
    client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
    criar_usuario_papel(app, "cozinheiro", "cozinha@example.com")
    cozinha = login(client, "cozinha@example.com")
    resposta = client.patch(
        f"/api/pedidos/{pedido_id}/status",
        json={"status": "Pronto para Entrega"},
        headers={"X-CSRF-Token": cozinha},
    )
    assert resposta.status_code == 409
    assert resposta.get_json()["codigo"] == "TRANSICAO_INVALIDA"


# ----------------------------- estoque -----------------------------
def test_estoque_lista_e_reposicao(app, client):
    with app.app_context():
        db.session.add(
            Ingrediente(nome="Arroz", unidade_medida="kg", quantidade_estoque=2, estoque_minimo=5)
        )
        db.session.commit()
    cadastrar_cliente(client)
    login(client, "cliente@example.com")
    assert client.get("/api/estoque").status_code == 403
    client.post("/api/auth/logout", headers={"X-CSRF-Token": token_csrf(client)})

    criar_usuario_papel(app, "administrador", "admin@example.com")
    token = login(client, "admin@example.com")
    item = client.get("/api/estoque").get_json()["dados"][0]
    assert item["abaixo_do_minimo"] is True

    resposta = client.post(
        f"/api/estoque/{item['id']}/repor", json={"quantidade": "10.5"}, headers={"X-CSRF-Token": token}
    )
    assert resposta.status_code == 200
    assert resposta.get_json()["dados"]["quantidade_estoque"] == 12.5
    assert client.get("/api/estoque?abaixo_do_minimo=true").get_json()["dados"] == []

    invalida = client.post(
        f"/api/estoque/{item['id']}/repor", json={"quantidade": -1}, headers={"X-CSRF-Token": token}
    )
    assert invalida.status_code == 400


# ----------------------------- agendamentos -----------------------------
def _bancada(app, status="Disponível"):
    with app.app_context():
        bancada = Bancada(identificacao="Bancada 01", valor_hora=Decimal("45.00"), status=status)
        db.session.add(bancada)
        db.session.commit()
        return bancada.id_bancada


def _horario(horas_a_partir=48, duracao=3):
    inicio = (datetime.now() + timedelta(hours=horas_a_partir)).replace(microsecond=0, second=0)
    fim = inicio + timedelta(hours=duracao)
    return inicio.isoformat(), fim.isoformat()


def test_agendamento_e_conflito_de_horario(app, client):
    bancada_id = _bancada(app)
    assert len(client.get("/api/bancadas").get_json()["dados"]) == 1

    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    inicio, fim = _horario()
    corpo = {"bancada_id": bancada_id, "data_hora_inicio": inicio, "data_hora_fim": fim}

    criado = client.post("/api/agendamentos", json=corpo, headers={"X-CSRF-Token": token})
    assert criado.status_code == 201

    repetido = client.post("/api/agendamentos", json=corpo, headers={"X-CSRF-Token": token})
    assert repetido.status_code == 409
    assert repetido.get_json()["codigo"] == "CONFLITO_HORARIO"

    meus = client.get("/api/agendamentos/meus").get_json()["dados"]
    assert len(meus) == 1

    cancelado = client.patch(
        f"/api/agendamentos/{meus[0]['id']}/cancelar", headers={"X-CSRF-Token": token}
    )
    assert cancelado.status_code == 200
    # horário liberado após o cancelamento
    novo = client.post("/api/agendamentos", json=corpo, headers={"X-CSRF-Token": token})
    assert novo.status_code == 201


def test_agendamento_invalido(app, client):
    bancada_id = _bancada(app)
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    inicio, fim = _horario()
    passado = (datetime.now() - timedelta(days=1)).isoformat()
    for corpo in (
        {"bancada_id": bancada_id, "data_hora_inicio": fim, "data_hora_fim": inicio},
        {"bancada_id": bancada_id, "data_hora_inicio": passado, "data_hora_fim": fim},
        {"bancada_id": bancada_id, "data_hora_inicio": "ontem", "data_hora_fim": fim},
        {"bancada_id": "1", "data_hora_inicio": inicio, "data_hora_fim": fim},
    ):
        resposta = client.post("/api/agendamentos", json=corpo, headers={"X-CSRF-Token": token})
        assert resposta.status_code == 400, corpo


def test_bancada_em_manutencao_nao_reserva(app, client):
    bancada_id = _bancada(app, status="Manutenção")
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    inicio, fim = _horario()
    resposta = client.post(
        "/api/agendamentos",
        json={"bancada_id": bancada_id, "data_hora_inicio": inicio, "data_hora_fim": fim},
        headers={"X-CSRF-Token": token},
    )
    assert resposta.status_code == 409


def test_cliente_nao_cancela_agendamento_de_outro(app, client):
    bancada_id = _bancada(app)
    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    inicio, fim = _horario()
    criado = client.post(
        "/api/agendamentos",
        json={"bancada_id": bancada_id, "data_hora_inicio": inicio, "data_hora_fim": fim},
        headers={"X-CSRF-Token": token},
    ).get_json()["dados"]
    client.post("/api/auth/logout", headers={"X-CSRF-Token": token})

    cadastrar_cliente(client, "outro@example.com")
    outro = login(client, "outro@example.com")
    resposta = client.patch(f"/api/agendamentos/{criado['id']}/cancelar", headers={"X-CSRF-Token": outro})
    assert resposta.status_code == 404


# ----------------------------- triggers do SQLite (database/20_triggers.sql) -----------------------------
def _estoque(app, ingrediente_id):
    with app.app_context():
        return db.session.get(Ingrediente, ingrediente_id).quantidade_estoque


def test_trigger_baixa_estoque_e_recusa_pedido_sem_estoque(app, client):
    prato_id = prato_como_admin(app, client)
    with app.app_context():
        arroz = Ingrediente(
            nome="Arroz", unidade_medida="kg", quantidade_estoque=Decimal("1.000"), estoque_minimo=Decimal("0")
        )
        db.session.add(arroz)
        db.session.flush()
        db.session.add(
            FichaTecnica(id_prato=prato_id, id_ingrediente=arroz.id_ingrediente, quantidade_utilizada=Decimal("0.400"))
        )
        db.session.commit()
        arroz_id = arroz.id_ingrediente

    cadastrar_cliente(client)
    token = login(client, "cliente@example.com")
    cabecalho = {"X-CSRF-Token": token}

    aceito = client.post("/api/pedidos", json={"itens": [{"prato_id": prato_id, "quantidade": 2}]}, headers=cabecalho)
    assert aceito.status_code == 201
    assert _estoque(app, arroz_id) == Decimal("0.200")  # 1.000 - 2 x 0.400

    recusado = client.post("/api/pedidos", json={"itens": [{"prato_id": prato_id, "quantidade": 1}]}, headers=cabecalho)
    assert recusado.status_code == 409
    assert recusado.get_json()["codigo"] == "ESTOQUE_INSUFICIENTE"
    assert _estoque(app, arroz_id) == Decimal("0.200")  # nada foi baixado
    assert len(client.get("/api/pedidos/meus").get_json()["dados"]) == 1  # pedido recusado não ficou gravado


def test_trigger_recalcula_total_do_pedido(app, client):
    prato_id = prato_como_admin(app, client)
    cliente_id = criar_usuario_papel(app, "cliente", "dono@example.com")
    with app.app_context():
        pedido = Pedido(id_usuario_cliente=cliente_id, valor_total=Decimal("0.00"))
        pedido.itens.append(ItemPedido(id_prato=prato_id, quantidade=2, preco_unitario=Decimal("10.00")))
        db.session.add(pedido)
        db.session.commit()
        pedido_id = pedido.id_pedido

        pedido.itens[0].quantidade = 5
        db.session.commit()

    with app.app_context():
        assert db.session.get(Pedido, pedido_id).valor_total == Decimal("50.00")


def test_trigger_barra_agendamento_sobreposto_mesmo_sem_a_verificacao_do_python(app):
    bancada_id = _bancada(app)
    cliente_id = criar_usuario_papel(app, "cliente", "dono@example.com")
    inicio = datetime.now() + timedelta(days=2)

    with app.app_context():
        db.session.add(
            Agendamento(
                id_usuario_cliente=cliente_id,
                id_bancada=bancada_id,
                data_hora_inicio=inicio,
                data_hora_fim=inicio + timedelta(hours=3),
            )
        )
        db.session.commit()

        db.session.add(
            Agendamento(
                id_usuario_cliente=cliente_id,
                id_bancada=bancada_id,
                data_hora_inicio=inicio + timedelta(hours=1),
                data_hora_fim=inicio + timedelta(hours=4),
            )
        )
        with pytest.raises(DBAPIError) as erro:
            db.session.commit()
        db.session.rollback()

        assert traduzir_erro_do_banco(erro.value).codigo == "CONFLITO_HORARIO"

        # reserva encostada (começa quando a outra termina) é permitida
        db.session.add(
            Agendamento(
                id_usuario_cliente=cliente_id,
                id_bancada=bancada_id,
                data_hora_inicio=inicio + timedelta(hours=3),
                data_hora_fim=inicio + timedelta(hours=5),
            )
        )
        db.session.commit()


def test_banco_com_dados_de_exemplo_permite_login_e_lista_33_pratos(app, client):
    criar_banco(com_dados=True)
    assert len(client.get("/api/menu").get_json()["dados"]) == 33
    login(client, "bruno.cliente@saborclic.com", senha="Senha@123")
    assert len(client.get("/api/pedidos/meus").get_json()["dados"]) == 4
    with app.app_context():
        # e-mail sem diferenciar maiúsculas (COLLATE NOCASE no SQLite)
        assert Usuario.query.filter_by(email="ANA.ADMIN@SABORCLIC.COM").first() is not None
        assert Prato.query.count() == 33
