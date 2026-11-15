from app.extensions import db


class Prato(db.Model):
    __tablename__ = "Prato"

    id_prato = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.String(500), nullable=False, default="")
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(50), nullable=False, default="Geral")
    disponivel = db.Column(db.Boolean, nullable=False, default=True)
    imagem_url = db.Column(db.String(500))
    id_usuario_admin = db.Column(
        db.Integer, db.ForeignKey("Administrador.id_usuario"), nullable=False
    )

    @property
    def id(self):
        return self.id_prato

    def to_dict(self):
        return {
            "id": self.id_prato,
            "prato_id": self.id_prato,
            "nome": self.nome,
            "descricao": self.descricao or "",
            "preco": float(self.preco),
            "categoria": self.categoria or "Geral",
            "imagem": self.imagem_url,
            "disponivel": self.disponivel,
            "ativo": self.disponivel,  # compatibilidade com o contrato anterior
        }
