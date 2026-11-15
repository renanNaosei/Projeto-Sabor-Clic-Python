from flask import flash, jsonify, request

from app.extensions import db
from app.models import Ingrediente
from app.security import resposta_erro
from app.services.erros import confirmar
from app.services.validacao_service import validar_reposicao


def listar_estoque():
    ingredientes = Ingrediente.query.order_by(Ingrediente.nome.asc()).all()
    apenas_baixo = request.args.get("abaixo_do_minimo", "").lower() == "true"
    dados = [i.to_dict() for i in ingredientes]
    if apenas_baixo:
        dados = [d for d in dados if d["abaixo_do_minimo"]]
    return jsonify({"sucesso": True, "dados": dados})


def repor_estoque(ingrediente_id):
    ingrediente = db.session.get(Ingrediente, ingrediente_id)
    if ingrediente is None:
        return resposta_erro("Ingrediente não encontrado.", 404, "NAO_ENCONTRADO")

    quantidade, erros = validar_reposicao(request.get_json(silent=True))
    if erros:
        return resposta_erro("Reposição inválida.", 400, "VALIDACAO", erros)

    ingrediente.quantidade_estoque = ingrediente.quantidade_estoque + quantidade
    confirmar()
    flash(f"Estoque de {ingrediente.nome} reposto.", "sucesso")
    return jsonify(
        {"sucesso": True, "mensagem": "Estoque atualizado.", "dados": ingrediente.to_dict()}
    )
