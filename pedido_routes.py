from flask import Blueprint

from app.controllers.pedido_controller import (
    atualizar_status,
    criar_novo_pedido,
    listar_todos,
    obter_pedido
)


pedido_bp = Blueprint(
    "pedidos",
    __name__
)


pedido_bp.get("")(
    listar_todos
)

pedido_bp.get("/<int:pedido_id>")(
    obter_pedido
)

pedido_bp.post("")(
    criar_novo_pedido
)

pedido_bp.put("/<int:pedido_id>/status")(
    atualizar_status
)