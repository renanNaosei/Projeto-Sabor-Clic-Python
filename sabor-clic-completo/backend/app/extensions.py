import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy(session_options={"expire_on_commit": False})


@event.listens_for(Engine, "connect")
def habilitar_chaves_estrangeiras_sqlite(conexao, _registro):
    """No modo reserva (SQLite) as FKs vêm desligadas por padrão; ligamos para manter a integridade."""
    if isinstance(conexao, sqlite3.Connection):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
