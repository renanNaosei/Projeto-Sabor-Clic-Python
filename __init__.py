from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app.routes.menu_routes import menu_bp
    from app.routes.pedido_routes import pedido_bp
    from app.routes.health_routes import health_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(menu_bp, url_prefix="/api/menu")
    app.register_blueprint(pedido_bp, url_prefix="/api/pedidos")

    @app.errorhandler(404)
    def not_found(_error):
        return {"sucesso": False, "erro": "Rota não encontrada"}, 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return {"sucesso": False, "erro": "Método HTTP não permitido"}, 405

    return app