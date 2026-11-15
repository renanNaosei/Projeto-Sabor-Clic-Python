from flask import Blueprint

from app.controllers.estoque_controller import listar_estoque, repor_estoque
from app.security import papeis_obrigatorios

estoque_bp = Blueprint("estoque", __name__)

estoque_bp.get("")(papeis_obrigatorios("cozinheiro", "administrador")(listar_estoque))
estoque_bp.post("/<int:ingrediente_id>/repor")(papeis_obrigatorios("administrador")(repor_estoque))
