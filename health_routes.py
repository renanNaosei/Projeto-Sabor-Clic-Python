from flask import Blueprint, jsonify


health_bp = Blueprint(
    "health",
    __name__
)


@health_bp.get("/api/health")
def health():
    return jsonify({
        "sucesso": True,
        "status": "online",
        "servico": "Sabor & Clic API"
    })