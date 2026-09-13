from flask import jsonify, request

from app.models.menu_model import (
    atualizar_prato,
    buscar_prato,
    criar_prato,
    listar_pratos,
    remover_prato,
)

from app.services.validacao_service import (
    validar_prato_payload
)


def listar_menu():
    apenas_ativos = (
        request.args.get("ativo", "false").lower() == "true"
    )

    return jsonify({
        "sucesso": True,
        "dados": listar_pratos(apenas_ativos)
    })


def obter_prato(prato_id):
    prato = buscar_prato(prato_id)

    if not prato:
        return jsonify({
            "sucesso": False,
            "erro": "Prato não encontrado"
        }), 404

    return jsonify({
        "sucesso": True,
        "dados": prato.to_dict()
    })


def criar_novo_prato():
    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "sucesso": False,
            "erro": "Corpo deve ser JSON"
        }), 400

    erros = validar_prato_payload(dados)

    if erros:
        return jsonify({
            "sucesso": False,
            "erros": erros
        }), 400

    prato = criar_prato(
        dados["nome"],
        dados["descricao"],
        dados["preco"],
        dados.get("ativo", True)
    )

    return jsonify({
        "sucesso": True,
        "mensagem": "Prato criado",
        "dados": prato.to_dict()
    }), 201


def editar_prato(prato_id):
    prato = buscar_prato(prato_id)

    if not prato:
        return jsonify({
            "sucesso": False,
            "erro": "Prato não encontrado"
        }), 404

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "sucesso": False,
            "erro": "Corpo deve ser JSON"
        }), 400

    erros = validar_prato_payload(
        dados,
        parcial=True
    )

    if erros:
        return jsonify({
            "sucesso": False,
            "erros": erros
        }), 400

    prato = atualizar_prato(
        prato,
        dados
    )

    return jsonify({
        "sucesso": True,
        "mensagem": "Prato atualizado",
        "dados": prato.to_dict()
    })


def excluir_prato(prato_id):
    prato = buscar_prato(prato_id)

    if not prato:
        return jsonify({
            "sucesso": False,
            "erro": "Prato não encontrado"
        }), 404

    remover_prato(prato)

    return jsonify({
        "sucesso": True,
        "mensagem": "Prato removido"
    })