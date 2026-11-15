from flask import Blueprint

from app.controllers.mensagens_controller import listar_mensagens

mensagens_bp = Blueprint("mensagens", __name__)
mensagens_bp.get("")(listar_mensagens)
