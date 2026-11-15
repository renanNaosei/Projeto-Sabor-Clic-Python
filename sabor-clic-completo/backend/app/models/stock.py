from app.extensions import db


class Ingrediente(db.Model):
    __tablename__ = "Ingrediente"

    id_ingrediente = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    unidade_medida = db.Column(db.String(10), nullable=False)
    quantidade_estoque = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    estoque_minimo = db.Column(db.Numeric(10, 3), nullable=False, default=0)

    def to_dict(self):
        return {
            "id": self.id_ingrediente,
            "nome": self.nome,
            "unidade_medida": self.unidade_medida,
            "quantidade_estoque": float(self.quantidade_estoque),
            "estoque_minimo": float(self.estoque_minimo),
            "abaixo_do_minimo": self.quantidade_estoque < self.estoque_minimo,
        }


class FichaTecnica(db.Model):
    __tablename__ = "Ficha_Tecnica"

    # PK composta (id_prato, id_ingrediente), igual ao banco.
    id_prato = db.Column(db.Integer, db.ForeignKey("Prato.id_prato"), primary_key=True)
    id_ingrediente = db.Column(
        db.Integer, db.ForeignKey("Ingrediente.id_ingrediente"), primary_key=True
    )
    quantidade_utilizada = db.Column(db.Numeric(10, 3), nullable=False)

    ingrediente = db.relationship("Ingrediente")
