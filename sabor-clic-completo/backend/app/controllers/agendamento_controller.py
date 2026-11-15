from flask import flash, jsonify, request

from app.extensions import db
from app.models import Agendamento, Bancada
from app.security import resposta_erro, usuario_atual
from app.services.erros import ErroDeNegocio, confirmar
from app.services.validacao_service import validar_agendamento


def listar_bancadas():
    bancadas = Bancada.query.order_by(Bancada.identificacao.asc()).all()
    return jsonify({"sucesso": True, "dados": [b.to_dict() for b in bancadas]})


def criar_agendamento():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return resposta_erro("O corpo deve ser JSON.", 400, "JSON_INVALIDO")

    valores, erros = validar_agendamento(dados)
    if erros:
        return resposta_erro("Agendamento inválido.", 400, "VALIDACAO", erros)
    bancada_id, inicio, fim = valores

    bancada = db.session.get(Bancada, bancada_id)
    if bancada is None:
        return resposta_erro("Bancada não encontrada.", 404, "NAO_ENCONTRADO")
    if bancada.status != "Disponível":
        raise ErroDeNegocio(f"A bancada está em estado '{bancada.status}'.", 409, "BANCADA_INDISPONIVEL")

    # Verificação prévia (mensagem amigável). O trigger do banco é a garantia final.
    conflito = Agendamento.query.filter(
        Agendamento.id_bancada == bancada_id,
        Agendamento.status != "Cancelado",
        Agendamento.data_hora_inicio < fim,
        Agendamento.data_hora_fim > inicio,
    ).first()
    if conflito:
        raise ErroDeNegocio(
            "Já existe uma reserva para esta bancada nesse horário.", 409, "CONFLITO_HORARIO"
        )

    agendamento = Agendamento(
        id_usuario_cliente=usuario_atual().id_usuario,
        id_bancada=bancada_id,
        data_hora_inicio=inicio,
        data_hora_fim=fim,
        status="Confirmado",
    )
    db.session.add(agendamento)
    confirmar()
    flash(f"Reserva da {bancada.identificacao} confirmada.", "sucesso")
    return jsonify(
        {"sucesso": True, "mensagem": "Agendamento confirmado.", "dados": agendamento.to_dict()}
    ), 201


def listar_meus_agendamentos():
    agendamentos = (
        Agendamento.query.filter_by(id_usuario_cliente=usuario_atual().id_usuario)
        .order_by(Agendamento.data_hora_inicio.desc())
        .all()
    )
    return jsonify({"sucesso": True, "dados": [a.to_dict() for a in agendamentos]})


def cancelar_agendamento(agendamento_id):
    agendamento = db.session.get(Agendamento, agendamento_id)
    if agendamento is None or agendamento.id_usuario_cliente != usuario_atual().id_usuario:
        return resposta_erro("Agendamento não encontrado.", 404, "NAO_ENCONTRADO")
    if agendamento.status != "Confirmado":
        raise ErroDeNegocio(
            f"Só é possível cancelar agendamentos confirmados (atual: {agendamento.status}).",
            409,
            "STATUS_INVALIDO",
        )
    agendamento.status = "Cancelado"
    confirmar()
    flash("Agendamento cancelado.", "info")
    return jsonify(
        {"sucesso": True, "mensagem": "Agendamento cancelado.", "dados": agendamento.to_dict()}
    )
