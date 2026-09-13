const API_BASE_URL = "http://127.0.0.1:5000/api";


async function requisicao(endpoint, opcoes = {}) {

    const resposta = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            headers: {
                "Content-Type": "application/json",
                ...(opcoes.headers || {})
            },
            ...opcoes
        }
    );

    const dados = await resposta.json();

    if (!resposta.ok) {
        throw new Error(
            dados.erro ||
            "Erro na comunicação com a API"
        );
    }

    return dados;
}


async function buscarMenu() {

    return requisicao(
        "/menu?ativo=true"
    );
}


async function criarPedido(clienteId, itens) {

    return requisicao(
        "/pedidos",
        {
            method: "POST",

            body: JSON.stringify({
                cliente_id: clienteId,
                itens: itens
            })
        }
    );
}