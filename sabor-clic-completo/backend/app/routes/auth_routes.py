from flask import Blueprint

from app.controllers.auth_controller import (
    entrar,
    obter_token_csrf,
    perfil_atual,
    registrar_cliente,
    sair,
)
from app.security import login_obrigatorio

auth_bp = Blueprint("auth", __name__)

auth_bp.get("/csrf")(obter_token_csrf)
auth_bp.post("/register")(registrar_cliente)
auth_bp.post("/login")(entrar)
auth_bp.post("/logout")(login_obrigatorio(sair))
auth_bp.get("/me")(perfil_atual)
