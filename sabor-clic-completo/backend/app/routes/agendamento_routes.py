from flask import Blueprint

from app.controllers.agendamento_controller import (
    cancelar_agendamento,
    criar_agendamento,
    listar_bancadas,
    listar_meus_agendamentos,
)
from app.security import papeis_obrigatorios

bancada_bp = Blueprint("bancadas", __name__)
agendamento_bp = Blueprint("agendamentos", __name__)
cliente = papeis_obrigatorios("cliente")

bancada_bp.get("")(listar_bancadas)
agendamento_bp.post("")(cliente(criar_agendamento))
agendamento_bp.get("/meus")(cliente(listar_meus_agendamentos))
agendamento_bp.patch("/<int:agendamento_id>/cancelar")(cliente(cancelar_agendamento))
