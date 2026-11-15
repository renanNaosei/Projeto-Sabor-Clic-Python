from flask import Blueprint

from app.controllers.menu_controller import (
    criar_novo_prato,
    editar_prato,
    excluir_prato,
    listar_menu,
    obter_prato,
)
from app.security import papeis_obrigatorios

menu_bp = Blueprint("menu", __name__)
admin = papeis_obrigatorios("administrador")

menu_bp.get("")(listar_menu)
menu_bp.get("/<int:prato_id>")(obter_prato)
menu_bp.post("")(admin(criar_novo_prato))

editar_prato_admin = admin(editar_prato)
menu_bp.put("/<int:prato_id>")(editar_prato_admin)
menu_bp.patch("/<int:prato_id>")(editar_prato_admin)
menu_bp.delete("/<int:prato_id>")(admin(excluir_prato))