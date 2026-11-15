from decimal import Decimal

from flask import flash, jsonify, request

from app.extensions import db
from app.models import Prato
from app.security import resposta_erro, usuario_atual
from app.services.erros import confirmar
from app.services.validacao_service import validar_prato_payload


def _eh_admin():
    usuario = usuario_atual()
    return usuario is not None and usuario.tipo_usuario == "administrador"


def listar_menu():
    # Visitantes e clientes veem só pratos disponíveis; o administrador pode usar ?ativo=false.
    consultar_todos = request.args.get("ativo", "true").lower() == "false" and _eh_admin()
    consulta = Prato.query
    if not consultar_todos:
        consulta = consulta.filter(Prato.disponivel.is_(True))
    pratos = consulta.order_by(Prato.id_prato.asc()).all()
    return jsonify({"sucesso": True, "dados": [prato.to_dict() for prato in pratos]})


def obter_prato(prato_id):
    prato = db.session.get(Prato, prato_id)
    if prato is None or (not prato.disponivel and not _eh_admin()):
        return resposta_erro("Prato não encontrado.", 404, "NAO_ENCONTRADO")
    return jsonify({"sucesso": True, "dados": prato.to_dict()})


def criar_novo_prato():
    dados = request.get_json(silent=True)
    erros = validar_prato_payload(dados)
    if erros:
        return resposta_erro("Dados do prato inválidos.", 400, "VALIDACAO", erros)

    prato = Prato(
        nome=dados["nome"].strip(),
        descricao=dados["descricao"].strip(),
        preco=Decimal(str(dados["preco"])).quantize(Decimal("0.01")),
        categoria=dados.get("categoria", "Geral").strip(),
        disponivel=dados.get("disponivel", dados.get("ativo", True)),
        imagem_url=(dados.get("imagem") or None),
        id_usuario_admin=usuario_atual().id_usuario,
    )
    db.session.add(prato)
    confirmar()
    flash(f"Prato '{prato.nome}' cadastrado.", "sucesso")
    return jsonify({"sucesso": True, "mensagem": "Prato cadastrado.", "dados": prato.to_dict()}), 201


def editar_prato(prato_id):
    prato = db.session.get(Prato, prato_id)
    if prato is None:
        return resposta_erro("Prato não encontrado.", 404, "NAO_ENCONTRADO")

    dados = request.get_json(silent=True)
    erros = validar_prato_payload(dados, parcial=True)
    if isinstance(dados, dict) and not dados:
        erros.append("Informe ao menos um campo para atualizar.")
    if erros:
        return resposta_erro("Dados do prato inválidos.", 400, "VALIDACAO", erros)

    if "nome" in dados:
        prato.nome = dados["nome"].strip()
    if "descricao" in dados:
        prato.descricao = dados["descricao"].strip()
    if "preco" in dados:
        prato.preco = Decimal(str(dados["preco"])).quantize(Decimal("0.01"))
    if "categoria" in dados:
        prato.categoria = dados["categoria"].strip()
    if "imagem" in dados:
        prato.imagem_url = dados["imagem"] or None
    if "disponivel" in dados or "ativo" in dados:
        prato.disponivel = dados.get("disponivel", dados.get("ativo"))

    confirmar()
    flash(f"Prato '{prato.nome}' atualizado.", "sucesso")
    return jsonify({"sucesso": True, "mensagem": "Prato atualizado.", "dados": prato.to_dict()})


def excluir_prato(prato_id):
    prato = db.session.get(Prato, prato_id)
    if prato is None:
        return resposta_erro("Prato não encontrado.", 404, "NAO_ENCONTRADO")

    # Exclusão lógica: preserva o histórico de pedidos (FK em Item_Pedido).
    prato.disponivel = False
    confirmar()
    flash(f"Prato '{prato.nome}' desativado.", "info")
    return jsonify({"sucesso": True, "mensagem": "Prato desativado."})
