from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

PAPEIS_VALIDOS = ("administrador", "cliente", "cozinheiro")


class Usuario(db.Model):
    __tablename__ = "Usuario"

    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.now)
    tipo_usuario = db.Column(db.String(20), nullable=False, default="cliente")
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    administrador = db.relationship(
        "Administrador", back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )
    cliente = db.relationship(
        "Cliente", back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )
    cozinheiro = db.relationship(
        "Cozinheiro", back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def id(self):
        return self.id_usuario

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha, method="scrypt")

    def conferir_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        dados = {
            "id": self.id_usuario,
            "nome": self.nome,
            "email": self.email,
            "tipo_usuario": self.tipo_usuario,
            "papel": self.tipo_usuario.upper(),  # compatibilidade com o contrato do Marco 2
            "ativo": self.ativo,
        }
        if self.tipo_usuario == "cliente" and self.cliente:
            dados["telefone"] = self.cliente.telefone
            dados["endereco_entrega"] = self.cliente.endereco_entrega
        elif self.tipo_usuario == "cozinheiro" and self.cozinheiro:
            dados["turno_trabalho"] = self.cozinheiro.turno_trabalho
            dados["especialidade"] = self.cozinheiro.especialidade
        elif self.tipo_usuario == "administrador" and self.administrador:
            dados["nivel_permissao"] = self.administrador.nivel_permissao
        return dados


class Administrador(db.Model):
    __tablename__ = "Administrador"

    id_usuario = db.Column(db.Integer, db.ForeignKey("Usuario.id_usuario"), primary_key=True)
    nivel_permissao = db.Column(db.String(30), nullable=False, default="TOTAL")

    usuario = db.relationship("Usuario", back_populates="administrador")


class Cliente(db.Model):
    __tablename__ = "Cliente"

    id_usuario = db.Column(db.Integer, db.ForeignKey("Usuario.id_usuario"), primary_key=True)
    endereco_entrega = db.Column(db.String(255))
    telefone = db.Column(db.String(20))

    usuario = db.relationship("Usuario", back_populates="cliente")


class Cozinheiro(db.Model):
    __tablename__ = "Cozinheiro"

    id_usuario = db.Column(db.Integer, db.ForeignKey("Usuario.id_usuario"), primary_key=True)
    turno_trabalho = db.Column(db.String(20), nullable=False, default="Manhã")
    especialidade = db.Column(db.String(100))

    usuario = db.relationship("Usuario", back_populates="cozinheiro")
