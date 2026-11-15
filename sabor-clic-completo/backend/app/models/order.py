from datetime import datetime
from decimal import Decimal

from app.extensions import db

STATUS_PEDIDO = (
    "Aguardando",
    "Iniciando Preparo",
    "Em Preparo",
    "Pronto para Entrega",
)


class Pedido(db.Model):
    __tablename__ = "Pedido"

    id_pedido = db.Column(db.Integer, primary_key=True)
    id_usuario_cliente = db.Column(
        db.Integer, db.ForeignKey("Cliente.id_usuario"), nullable=False
    )
    id_usuario_cozinheiro = db.Column(
        db.Integer, db.ForeignKey("Cozinheiro.id_usuario"), nullable=True
    )
    data_hora_pedido = db.Column(db.DateTime, nullable=False, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default="Aguardando")
    valor_total = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    observacoes = db.Column(db.String(300))

    itens = db.relationship(
        "ItemPedido",
        back_populates="pedido",
        cascade="all, delete-orphan",
        order_by="ItemPedido.id_item_pedido",
    )

    @property
    def id(self):
        return self.id_pedido

    def calcular_total(self):
        return sum(
            (item.preco_unitario * item.quantidade for item in self.itens),
            start=Decimal("0.00"),
        ).quantize(Decimal("0.01"))

    def to_dict(self, incluir_itens=True):
        dados = {
            "id": self.id_pedido,
            "pedido_id": self.id_pedido,
            "cliente_id": self.id_usuario_cliente,
            "cozinheiro_id": self.id_usuario_cozinheiro,
            "data_hora_pedido": self.data_hora_pedido.isoformat() if self.data_hora_pedido else None,
            "status": self.status,
            "valor_total": f"{self.valor_total:.2f}",
            "observacoes": self.observacoes,
        }
        if incluir_itens:
            dados["itens"] = [item.to_dict() for item in self.itens]
        return dados


class ItemPedido(db.Model):
    __tablename__ = "Item_Pedido"

    id_item_pedido = db.Column(db.Integer, primary_key=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey("Pedido.id_pedido"), nullable=False)
    id_prato = db.Column(db.Integer, db.ForeignKey("Prato.id_prato"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    tempo_estimado_preparo = db.Column(db.Integer, default=15)

    pedido = db.relationship("Pedido", back_populates="itens")
    prato = db.relationship("Prato")

    def to_dict(self):
        return {
            "id": self.id_item_pedido,
            "prato_id": self.id_prato,
            "nome": self.prato.nome if self.prato else "Prato removido",
            "quantidade": self.quantidade,
            "preco_unitario": f"{self.preco_unitario:.2f}",
            "subtotal": f"{self.preco_unitario * self.quantidade:.2f}",
            "tempo_estimado_preparo": self.tempo_estimado_preparo,
        }
