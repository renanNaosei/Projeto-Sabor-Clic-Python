"""Criação do banco SQLite a partir dos scripts da pasta database/.

Os scripts SQL continuam sendo a fonte do schema (tabelas, restrições, triggers);
este módulo só os executa na ordem certa. O SQLAlchemy não cria tabelas.
"""
from pathlib import Path

from app.extensions import db

PASTA_SQL = Path(__file__).resolve().parents[2] / "database"
SCRIPTS_ESTRUTURA = ("01_modelo_fisico.sql", "20_triggers.sql")
SCRIPT_DADOS = "02_insercoes_basicas.sql"


def banco_tem_dados():
    """True se a tabela Usuario já existe e tem linhas (evita apagar dados sem querer)."""
    try:
        return db.session.execute(db.text("SELECT COUNT(*) FROM Usuario")).scalar() > 0
    except Exception:
        db.session.rollback()
        return False


def criar_banco(com_dados=True):
    """Recria o banco do zero: 01 (tabelas) -> 02 (dados, opcional) -> 20 (triggers).

    A ordem importa: os dados de exemplo entram antes dos triggers para não
    gerar baixa de estoque nos pedidos históricos.
    """
    scripts = [SCRIPTS_ESTRUTURA[0]]
    if com_dados:
        scripts.append(SCRIPT_DADOS)
    scripts.append(SCRIPTS_ESTRUTURA[1])

    conexao = db.engine.raw_connection()
    try:
        for nome in scripts:
            conexao.executescript((PASTA_SQL / nome).read_text(encoding="utf-8"))
        conexao.commit()
    finally:
        conexao.close()
    db.session.remove()
    return scripts
