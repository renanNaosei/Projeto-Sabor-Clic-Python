from decimal import Decimal

from flask import flash, jsonify, request

from app.extensions import db
from app.models import ItemPedido, Pedido, Prato
from app.security import resposta_erro, usuario_atual
from app.services.erros import confirmar
from app.services.validacao_service import validar_itens_pedido, validar_observacoes

TRANSICOES_PERMITIDAS = {
    "Aguardando": {"Iniciando Preparo"},
    "Iniciando Preparo": {"Em Preparo"},
    "Em Preparo": {"Pronto para Entrega"},
    "Pronto para Entrega": set(),
}


def criar_novo_pedido():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return resposta_erro("O corpo deve ser JSON.", 400, "JSON_INVALIDO")

    usuario = usuario_atual()

    # O cliente vem da sessão. Se o JSON trouxer outro cliente_id, recusamos.
    enviado = dados.get("cliente_id")
    if enviado is not None:
        try:
            divergente = isinstance(enviado, bool) or int(enviado) != usuario.id_usuario
        except (TypeError, ValueError):
            return resposta_erro("cliente_id inválido.", 400, "VALIDACAO")
        if divergente:
            return resposta_erro(
                "Não é permitido criar pedidos em nome de outro cliente.", 403, "CLIENTE_DIVERGENTE"
            )

    quantidades, erros = validar_itens_pedido(dados.get("itens"))
    observacoes, erros_obs = validar_observacoes(dados.get("observacoes"))
    erros = (erros or []) + erros_obs
    if erros:
        return resposta_erro("Pedido inválido.", 400, "VALIDACAO", erros)

    pratos = Prato.query.filter(
        Prato.id_prato.in_(list(quantidades)), Prato.disponivel.is_(True)
    ).all()
    por_id = {prato.id_prato: prato for prato in pratos}
    indisponiveis = sorted(set(quantidades) - set(por_id))
    if indisponiveis:
        return resposta_erro(
            "Um ou mais pratos não existem ou estão indisponíveis.",
            409,
            "PRATOS_INDISPONIVEIS",
            {"prato_ids": indisponiveis},
        )

    pedido = Pedido(
        id_usuario_cliente=usuario.id_usuario,
        status="Aguardando",
        valor_total=Decimal("0.00"),
        observacoes=observacoes,
    )
    for prato_id, quantidade in quantidades.items():
        prato = por_id[prato_id]
        pedido.itens.append(
            ItemPedido(
                prato=prato,
                quantidade=quantidade,
                preco_unitario=prato.preco,  # sempre o preço do banco, nunca o do navegador
                tempo_estimado_preparo=15,
            )
        )
    pedido.valor_total = pedido.calcular_total()

    db.session.add(pedido)
    confirmar()  # trigger de estoque pode recusar com 409
    db.session.refresh(pedido)  # o trigger recalcula valor_total no banco

    flash(f"Pedido #{pedido.id_pedido} enviado para a cozinha.", "sucesso")
    return jsonify(
        {
            "sucesso": True,
            "mensagem": "Pedido registrado e enviado para a fila da cozinha.",
            "dados": pedido.to_dict(),
        }
    ), 201


def listar_pedidos_cozinha():
    consulta = Pedido.query
    status = request.args.get("status")
    if status:
        if status not in TRANSICOES_PERMITIDAS:
            return resposta_erro("Status inválido.", 400, "STATUS_INVALIDO")
        consulta = consulta.filter(Pedido.status == status)
    pedidos = consulta.order_by(Pedido.data_hora_pedido.asc(), Pedido.id_pedido.asc()).all()
    return jsonify({"sucesso": True, "dados": [p.to_dict() for p in pedidos]})


def listar_meus_pedidos():
    pedidos = (
        Pedido.query.filter_by(id_usuario_cliente=usuario_atual().id_usuario)
        .order_by(Pedido.data_hora_pedido.desc(), Pedido.id_pedido.desc())
        .all()
    )
    return jsonify({"sucesso": True, "dados": [p.to_dict() for p in pedidos]})


def obter_pedido(pedido_id):
    pedido = db.session.get(Pedido, pedido_id)
    usuario = usuario_atual()
    # 404 (e não 403) para pedidos alheios: não revela que o número existe.
    if pedido is None or (
        usuario.tipo_usuario == "cliente" and pedido.id_usuario_cliente != usuario.id_usuario
    ):
        return resposta_erro("Pedido não encontrado.", 404, "NAO_ENCONTRADO")
    return jsonify({"sucesso": True, "dados": pedido.to_dict()})


def atualizar_status(pedido_id):
    pedido = db.session.get(Pedido, pedido_id)
    if pedido is None:
        return resposta_erro("Pedido não encontrado.", 404, "NAO_ENCONTRADO")

    dados = request.get_json(silent=True)
    novo = dados.get("status") if isinstance(dados, dict) else None
    if novo not in TRANSICOES_PERMITIDAS:
        return resposta_erro("Status inválido.", 400, "STATUS_INVALIDO")
    if novo not in TRANSICOES_PERMITIDAS.get(pedido.status, set()):
        return resposta_erro(
            f"Transição não permitida: {pedido.status} -> {novo}.", 409, "TRANSICAO_INVALIDA"
        )

    pedido.status = novo
    if pedido.id_usuario_cozinheiro is None:
        pedido.id_usuario_cozinheiro = usuario_atual().id_usuario
    confirmar()
    flash(f"Pedido #{pedido.id_pedido}: {novo}.", "info")
    return jsonify(
        {"sucesso": True, "mensagem": "Status do pedido atualizado.", "dados": pedido.to_dict()}
    )
