def validar_prato_payload(dados, parcial=False):
    erros = []

    obrigatorios = [
        "nome",
        "descricao",
        "preco"
    ]

    if not parcial:
        for campo in obrigatorios:
            if campo not in dados:
                erros.append(
                    f"Campo obrigatório: {campo}"
                )

    if "nome" in dados:
        if (
            not isinstance(dados["nome"], str)
            or not dados["nome"].strip()
        ):
            erros.append(
                "nome deve ser um texto não vazio"
            )

    if "descricao" in dados:
        if not isinstance(dados["descricao"], str):
            erros.append(
                "descricao deve ser um texto"
            )

    if "preco" in dados:
        try:
            preco = float(dados["preco"])

            if preco < 0:
                erros.append(
                    "preco não pode ser negativo"
                )

        except (TypeError, ValueError):
            erros.append(
                "preco deve ser numérico"
            )

    if "ativo" in dados:
        if not isinstance(dados["ativo"], bool):
            erros.append(
                "ativo deve ser booleano"
            )

    return erros