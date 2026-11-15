from app.extensions import db


class Bancada(db.Model):
    __tablename__ = "Bancada"

    id_bancada = db.Column(db.Integer, primary_key=True)
    identificacao = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    capacidade = db.Column(db.Integer)
    equipamentos = db.Column(db.String(255))
    valor_hora = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Disponível")

    def to_dict(self):
        return {
            "id": self.id_bancada,
            "identificacao": self.identificacao,
            "descricao": self.descricao,
            "capacidade": self.capacidade,
            "equipamentos": self.equipamentos,
            "valor_hora": float(self.valor_hora),
            "status": self.status,
        }


class Agendamento(db.Model):
    __tablename__ = "Agendamento"

    id_agendamento = db.Column(db.Integer, primary_key=True)
    id_usuario_cliente = db.Column(
        db.Integer, db.ForeignKey("Cliente.id_usuario"), nullable=False
    )
    id_bancada = db.Column(db.Integer, db.ForeignKey("Bancada.id_bancada"), nullable=False)
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Confirmado")

    bancada = db.relationship("Bancada")

    def to_dict(self):
        return {
            "id": self.id_agendamento,
            "cliente_id": self.id_usuario_cliente,
            "bancada_id": self.id_bancada,
            "bancada": self.bancada.identificacao if self.bancada else None,
            "data_hora_inicio": self.data_hora_inicio.isoformat(),
            "data_hora_fim": self.data_hora_fim.isoformat(),
            "status": self.status,
        }
