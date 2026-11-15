import re

from sqlalchemy.exc import DBAPIError

from app.extensions import db


class ErroDeNegocio(Exception):
    """Regra de negócio violada. O handler global devolve JSON com o status indicado."""

    def __init__(self, mensagem, status=400, codigo="REGRA_DE_NEGOCIO", detalhes=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status
        self.codigo = codigo
        self.detalhes = detalhes


# O SQLite não tem THROW com número: os triggers usam RAISE(ABORT, 'texto fixo')
# (database/20_triggers.sql). O backend reconhece o erro por esse texto.
_ERROS_DOS_TRIGGERS = (
    ("Estoque insuficiente", "ESTOQUE_INSUFICIENTE"),
    ("Conflito de horário", "CONFLITO_HORARIO"),
)


def traduzir_erro_do_banco(erro):
    """Se o erro veio de um RAISE(ABORT) dos triggers devolve ErroDeNegocio 409; senão, None."""
    if not isinstance(erro, DBAPIError):
        return None

    texto = str(getattr(erro, "orig", erro)).strip()
    for trecho, codigo in _ERROS_DOS_TRIGGERS:
        if texto.startswith(trecho):
            return ErroDeNegocio(texto, 409, codigo)
    return None


def confirmar():
    """commit() que converte erros dos triggers em ErroDeNegocio (409) e faz rollback."""
    try:
        db.session.commit()
    except DBAPIError as erro:
        db.session.rollback()
        traduzido = traduzir_erro_do_banco(erro)
        if traduzido is not None:
            raise traduzido from erro
        raise


def limpar_texto(valor, limite):
    return re.sub(r"\s+", " ", str(valor)).strip()[:limite]
