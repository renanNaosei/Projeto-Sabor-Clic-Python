"""Testes que não precisam de banco: validação e tradução dos erros dos triggers."""
import sqlite3

from sqlalchemy.exc import DBAPIError

from app.services.erros import traduzir_erro_do_banco
from app.services.validacao_service import validar_itens_pedido, validar_reposicao


def _erro_do_banco(mensagem):
    return DBAPIError("INSERT ...", {}, sqlite3.IntegrityError(mensagem))


def test_traduz_erro_de_estoque_para_409():
    traduzido = traduzir_erro_do_banco(
        _erro_do_banco("Estoque insuficiente de ingrediente para este pedido.")
    )
    assert traduzido.status == 409
    assert traduzido.codigo == "ESTOQUE_INSUFICIENTE"
    assert traduzido.mensagem == "Estoque insuficiente de ingrediente para este pedido."


def test_traduz_conflito_de_horario_para_409():
    traduzido = traduzir_erro_do_banco(
        _erro_do_banco("Conflito de horário: a bancada já está reservada neste período.")
    )
    assert traduzido.status == 409
    assert traduzido.codigo == "CONFLITO_HORARIO"


def test_erro_comum_do_banco_nao_e_traduzido():
    assert traduzir_erro_do_banco(_erro_do_banco("UNIQUE constraint failed: Usuario.email")) is None
    assert traduzir_erro_do_banco(ValueError("x")) is None


def test_validar_itens_aceita_alias_id_prato():
    quantidades, erros = validar_itens_pedido([{"id_prato": 3, "quantidade": 2}])
    assert erros == [] and quantidades == {3: 2}


def test_validar_itens_limita_linhas():
    _, erros = validar_itens_pedido([{"prato_id": 1, "quantidade": 1}] * 31)
    assert erros


def test_validar_reposicao():
    assert validar_reposicao({"quantidade": "2.5"})[1] == []
    assert validar_reposicao({"quantidade": 0})[1]
    assert validar_reposicao({"quantidade": True})[1]
    assert validar_reposicao({})[1]
