from flask import Blueprint

from app.controllers.menu_controller import (
    criar_novo_prato,
    editar_prato,
    excluir_prato,
    listar_menu,
    obter_prato
)


menu_bp = Blueprint(
    "menu",
    __name__
)


menu_bp.get("")(
    listar_menu
)

menu_bp.get("/<int:prato_id>")(
    obter_prato
)

menu_bp.post("")(
    criar_novo_prato
)

menu_bp.put("/<int:prato_id>")(
    editar_prato
)

menu_bp.delete("/<int:prato_id>")(
    excluir_prato
)