"""Validação de entrada (nunca confiar no JSON recebido)."""
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

MAX_ITENS_POR_PEDIDO = 30
MAX_QUANTIDADE_POR_ITEM = 99
MAX_OBSERVACOES = 300
CAMPOS_PRATO = {"nome", "descricao", "preco", "categoria", "disponivel", "ativo", "imagem"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DURACAO_MAXIMA_AGENDAMENTO = timedelta(hours=12)


def _eh_inteiro(valor):
    # bool é subclasse de int em Python; rejeitado explicitamente.
    return isinstance(valor, int) and not isinstance(valor, bool)


def _decimal(valor):
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return numero if numero.is_finite() else None


def validar_imagem(valor):
    if valor is None or valor == "":
        return None
    if not isinstance(valor, str) or len(valor) > 500:
        return "imagem deve ser um texto com até 500 caracteres."
    if not (valor.startswith(("https://", "http://", "/")) or valor.startswith("img/")):
        return "imagem deve ser uma URL http(s) ou um caminho relativo."
    return None


def validar_cadastro(dados):
    erros = []
    nome, email, senha = dados.get("nome"), dados.get("email"), dados.get("senha")
    if not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 150:
        erros.append("nome é obrigatório e deve ter até 150 caracteres.")
    if not isinstance(email, str) or len(email.strip()) > 150 or not EMAIL_RE.match(email.strip()):
        erros.append("Informe um e-mail válido.")
    if not isinstance(senha, str) or not 8 <= len(senha) <= 128:
        erros.append("senha deve possuir entre 8 e 128 caracteres.")
    for campo, limite in (("telefone", 20), ("endereco_entrega", 255)):
        valor = dados.get(campo)
        if valor is not None and (not isinstance(valor, str) or len(valor) > limite):
            erros.append(f"{campo} deve ser um texto com até {limite} caracteres.")
    return erros


def validar_prato_payload(dados, parcial=False):
    if not isinstance(dados, dict):
        return ["O corpo da requisição deve ser um objeto JSON."]

    erros = []
    desconhecidos = sorted(set(dados) - CAMPOS_PRATO)
    if desconhecidos:
        erros.append("Campos não permitidos: " + ", ".join(desconhecidos))

    if not parcial:
        for campo in ("nome", "descricao", "preco"):
            if campo not in dados:
                erros.append(f"Campo obrigatório: {campo}.")

    if "nome" in dados:
        nome = dados["nome"]
        if not isinstance(nome, str) or not nome.strip():
            erros.append("nome deve ser um texto não vazio.")
        elif len(nome.strip()) > 150:
            erros.append("nome deve ter no máximo 150 caracteres.")

    if "descricao" in dados:
        descricao = dados["descricao"]
        if not isinstance(descricao, str):
            erros.append("descricao deve ser um texto.")
        elif len(descricao) > 500:
            erros.append("descricao deve ter no máximo 500 caracteres.")

    if "categoria" in dados:
        categoria = dados["categoria"]
        if not isinstance(categoria, str) or not categoria.strip():
            erros.append("categoria deve ser um texto não vazio.")
        elif len(categoria.strip()) > 50:
            erros.append("categoria deve ter no máximo 50 caracteres.")

    if "preco" in dados:
        valor = None if isinstance(dados["preco"], bool) else _decimal(dados["preco"])
        if valor is None:
            erros.append("preco deve ser numérico.")
        elif valor < 0:
            erros.append("preco deve ser maior ou igual a zero.")
        elif valor.as_tuple().exponent < -2:
            erros.append("preco aceita no máximo duas casas decimais.")
        elif valor > Decimal("99999999.99"):
            erros.append("preco excede o limite permitido.")

    if "imagem" in dados:
        erro_imagem = validar_imagem(dados["imagem"])
        if erro_imagem:
            erros.append(erro_imagem)

    if "ativo" in dados and "disponivel" in dados:
        erros.append("Envie apenas um dos campos: ativo ou disponivel.")
    for campo in ("ativo", "disponivel"):
        if campo in dados and not isinstance(dados[campo], bool):
            erros.append(f"{campo} deve ser booleano.")

    return erros


def validar_itens_pedido(itens):
    """Devolve ({prato_id: quantidade}, erros). Linhas repetidas do mesmo prato são somadas."""
    if not isinstance(itens, list) or not itens:
        return None, ["Informe ao menos um item no pedido."]
    if len(itens) > MAX_ITENS_POR_PEDIDO:
        return None, [f"Um pedido pode conter no máximo {MAX_ITENS_POR_PEDIDO} linhas de itens."]

    quantidades, erros = {}, []
    for indice, item in enumerate(itens, start=1):
        if not isinstance(item, dict):
            erros.append(f"Item {indice}: deve ser um objeto.")
            continue
        prato_id = item.get("prato_id", item.get("id_prato"))
        quantidade = item.get("quantidade")
        if not _eh_inteiro(prato_id) or prato_id <= 0:
            erros.append(f"Item {indice}: prato_id deve ser um inteiro positivo.")
            continue
        if not _eh_inteiro(quantidade) or not 1 <= quantidade <= MAX_QUANTIDADE_POR_ITEM:
            erros.append(
                f"Item {indice}: quantidade deve ser um inteiro entre 1 e {MAX_QUANTIDADE_POR_ITEM}."
            )
            continue
        quantidades[prato_id] = quantidades.get(prato_id, 0) + quantidade

    for prato_id, total in quantidades.items():
        if total > MAX_QUANTIDADE_POR_ITEM:
            erros.append(
                f"A quantidade total do prato {prato_id} não pode exceder {MAX_QUANTIDADE_POR_ITEM}."
            )

    return (quantidades if not erros else None), erros


def validar_observacoes(valor):
    """Devolve (texto_ou_None, erros)."""
    if valor is None:
        return None, []
    if not isinstance(valor, str):
        return None, ["observacoes deve ser um texto."]
    texto = " ".join(valor.split())
    if len(texto) > MAX_OBSERVACOES:
        return None, [f"observacoes deve ter no máximo {MAX_OBSERVACOES} caracteres."]
    return (texto or None), []


def _data(valor):
    if not isinstance(valor, str):
        return None
    try:
        data = datetime.fromisoformat(valor.strip().replace("Z", ""))
    except ValueError:
        return None
    return data.replace(tzinfo=None)


def validar_agendamento(dados):
    """Devolve ((id_bancada, inicio, fim), erros)."""
    erros = []
    bancada_id = dados.get("bancada_id", dados.get("id_bancada"))
    if not _eh_inteiro(bancada_id) or bancada_id <= 0:
        erros.append("bancada_id deve ser um inteiro positivo.")

    inicio = _data(dados.get("data_hora_inicio"))
    fim = _data(dados.get("data_hora_fim"))
    if inicio is None:
        erros.append("data_hora_inicio deve estar no formato ISO 8601 (ex.: 2026-12-01T09:00).")
    if fim is None:
        erros.append("data_hora_fim deve estar no formato ISO 8601 (ex.: 2026-12-01T12:00).")

    if inicio and fim:
        if fim <= inicio:
            erros.append("data_hora_fim deve ser posterior a data_hora_inicio.")
        elif fim - inicio > DURACAO_MAXIMA_AGENDAMENTO:
            erros.append("Um agendamento pode durar no máximo 12 horas.")
        if inicio < datetime.now():
            erros.append("Não é possível agendar no passado.")

    return ((bancada_id, inicio, fim) if not erros else None), erros


def validar_reposicao(dados):
    """Devolve (quantidade_decimal, erros)."""
    if not isinstance(dados, dict) or "quantidade" not in dados:
        return None, ["Informe a quantidade a repor."]
    valor = None if isinstance(dados["quantidade"], bool) else _decimal(dados["quantidade"])
    if valor is None or valor <= 0:
        return None, ["quantidade deve ser um número maior que zero."]
    if valor.as_tuple().exponent < -3:
        return None, ["quantidade aceita no máximo três casas decimais."]
    if valor > Decimal("100000"):
        return None, ["quantidade excede o limite permitido por reposição."]
    return valor, []
