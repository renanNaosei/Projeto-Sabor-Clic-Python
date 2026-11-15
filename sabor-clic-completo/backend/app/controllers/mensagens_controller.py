from flask import get_flashed_messages, jsonify


def listar_mensagens():
    """Flash Messages adaptadas à API: devolve (e consome) as mensagens da sessão."""
    mensagens = [
        {"categoria": categoria, "texto": texto}
        for categoria, texto in get_flashed_messages(with_categories=True)
    ]
    return jsonify({"sucesso": True, "dados": mensagens})
