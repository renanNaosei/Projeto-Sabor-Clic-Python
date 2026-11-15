from flask import Blueprint

from app.controllers.pedido_controller import (
    atualizar_status,
    criar_novo_pedido,
    listar_meus_pedidos,
    listar_pedidos_cozinha,
    obter_pedido,
)
from app.security import papeis_obrigatorios

pedido_bp = Blueprint("pedidos", __name__)

pedido_bp.post("")(papeis_obrigatorios("cliente")(criar_novo_pedido))
pedido_bp.get("")(papeis_obrigatorios("cozinheiro", "administrador")(listar_pedidos_cozinha))
pedido_bp.get("/meus")(papeis_obrigatorios("cliente")(listar_meus_pedidos))
pedido_bp.get("/<int:pedido_id>")(
    papeis_obrigatorios("cliente", "cozinheiro", "administrador")(obter_pedido)
)

atualizar_status_cozinha = papeis_obrigatorios("cozinheiro")(atualizar_status)
pedido_bp.patch("/<int:pedido_id>/status")(atualizar_status_cozinha)
pedido_bp.put("/<int:pedido_id>/status")(atualizar_status_cozinha)