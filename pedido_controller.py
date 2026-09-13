from flask import jsonify, request

from app.models.pedido_model import (
    buscar_pedido,
    criar_pedido,
    listar_pedidos
)


STATUS_VALIDOS = {
    "Aguardando",
    "Iniciando Preparo",
    "Em Preparo",
    "Pronto para Entrega"
}


def listar_todos():
    return jsonify({
        "sucesso": True,
        "dados": listar_pedidos()
    })


def criar_novo_pedido():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "sucesso": False,
            "erro": "Corpo deve ser JSON"
        }), 400

    cliente_id = dados.get("cliente_id")
    itens = dados.get("itens")

    if not cliente_id or not isinstance(itens, list) or not itens:
        return jsonify({
            "sucesso": False,
            "erro": "cliente_id e itens são obrigatórios"
        }), 400

    pedido = criar_pedido(
        cliente_id,
        itens
    )

    return jsonify({
        "sucesso": True,
        "mensagem": "Pedido criado",
        "dados": pedido.to_dict()
    }), 201


def obter_pedido(pedido_id):
    pedido = buscar_pedido(pedido_id)

    if not pedido:
        return jsonify({
            "sucesso": False,
            "erro": "Pedido não encontrado"
        }), 404

    return jsonify({
        "sucesso": True,
        "dados": pedido.to_dict()
    })


def atualizar_status(pedido_id):
    pedido = buscar_pedido(pedido_id)

    if not pedido:
        return jsonify({
            "sucesso": False,
            "erro": "Pedido não encontrado"
        }), 404

    dados = request.get_json(silent=True)

    status = (
        dados.get("status")
        if isinstance(dados, dict)
        else None
    )

    if status not in STATUS_VALIDOS:
        return jsonify({
            "sucesso": False,
            "erro": "Status inválido"
        }), 400

    pedido.status = status

    return jsonify({
        "sucesso": True,
        "mensagem": "Status atualizado",
        "dados": pedido.to_dict()
    })