// ===========================================================
// 1. ARRAY DE OBJETOS — CARDÁPIO
// ===========================================================
// Guarda os pratos disponíveis. O array em si nunca é reatribuído
// (só temos métodos que leem ou transformam o conteúdo) — por isso "const".
const cardapio = [
    { nome: "Hambúrguer", preco: 25, categoria: "Lanche" },
    { nome: "Pizza", preco: 40, categoria: "Pizza" },
    { nome: "Lasanha", preco: 30, categoria: "Massas" },
];

// ===========================================================
// 2. ARRAY DO CARRINHO
// ===========================================================
// Este SIM precisa de "let": é reatribuído em removerDoCarrinho()
// (carrinho = carrinho.filter(...)) e ao finalizar o pedido.
let carrinho = [];

// ===========================================================
// 3. ACESSANDO UM OBJETO
// ===========================================================
const primeiroPrato = cardapio[0];
console.log(primeiroPrato.nome);
// Hambúrguer

// ===========================================================
// 4. FOR...OF — percorre os VALORES de um array
// ===========================================================
for (const prato of cardapio) {
    console.log(prato.nome);
}
// Hambúrguer / Pizza / Lasanha

// ===========================================================
// 5. FOR...IN — percorre as CHAVES de um objeto
// ===========================================================
for (const propriedade in primeiroPrato) {
    console.log(propriedade);
}
// nome / preco / categoria

// ===========================================================
// 6. FOREACH — executa uma função para cada item do array
// ===========================================================
cardapio.forEach(({ nome, preco }) => {
    console.log(nome + " - R$ " + preco);
});

// ===========================================================
// 7. MAP — transforma cada item e devolve um NOVO array
// ===========================================================
// Não altera "cardapio": aqui geramos só a lista de nomes.
const nomesDoCardapio = cardapio.map((prato) => prato.nome);
console.log(nomesDoCardapio);
// ["Hambúrguer", "Pizza", "Lasanha"]

// ===========================================================
// 8. FILTER — devolve só os itens que passam numa condição
// ===========================================================
const pratosAteTrinta = cardapio.filter((prato) => prato.preco <= 30);
console.log(pratosAteTrinta);
// Hambúrguer e Lasanha

// ===========================================================
// 9. REDUCE — acumula todo o array em um único valor
// ===========================================================
const precoTotalCardapio = cardapio.reduce((soma, prato) => soma + prato.preco, 0);
console.log(precoTotalCardapio);
// 95

// ===========================================================
// 10. PEGANDO ELEMENTOS DO HTML
// ===========================================================
const areaCardapio = document.getElementById("cardapio");
const areaCarrinho = document.getElementById("carrinho");
const areaTotal = document.getElementById("total");

// ===========================================================
// 11. FUNÇÃO PARA MOSTRAR O CARDÁPIO
// ===========================================================
function mostrarCardapio() {
    areaCardapio.innerHTML = "";

    // map: cria um array de elementos <div>, um por prato.
    const cards = cardapio.map((prato, indice) => {
        const { nome, categoria, preco } = prato;

        const card = document.createElement("div");
        card.innerHTML = `
            <h2>${nome}</h2>
            <p>Categoria: ${categoria}</p>
            <p>Preço: R$ ${preco.toFixed(2)}</p>
        `;

        // addEventListener no lugar de onclick inline: funções dentro de
        // módulos (Parte 2) não ficam acessíveis para atributos do HTML.
        const botao = document.createElement("button");
        botao.textContent = "Adicionar ao carrinho";
        botao.addEventListener("click", () => adicionarCarrinho(indice));
        card.appendChild(botao);

        return card;
    });

    cards.forEach((card) => areaCardapio.appendChild(card));
}

// ===========================================================
// 12. ADICIONAR PRODUTO AO CARRINHO
// ===========================================================
function adicionarCarrinho(indice) {
    const pratoEscolhido = cardapio[indice];
    const { nome, preco } = pratoEscolhido;

    const produtoExistente = carrinho.find((item) => item.nome === nome);

    if (produtoExistente) {
        produtoExistente.quantidade++;
    } else {
        const produtoCarrinho = { nome, preco, quantidade: 1 };
        carrinho.push(produtoCarrinho);
    }

    mostrarCarrinho();
}

// ===========================================================
// 13. REMOVER PRODUTO DO CARRINHO
// ===========================================================
function removerDoCarrinho(nomeProduto) {
    // filter: mantém no carrinho só os itens diferentes do removido.
    carrinho = carrinho.filter((item) => item.nome !== nomeProduto);
    mostrarCarrinho();
}

// ===========================================================
// 14. MOSTRAR O CARRINHO
// ===========================================================
function mostrarCarrinho() {
    areaCarrinho.innerHTML = "";

    // reduce: soma preco * quantidade de todos os itens num único valor.
    const total = carrinho.reduce((soma, item) => soma + item.preco * item.quantidade, 0);

    carrinho.forEach((item) => {
        const { nome, preco, quantidade } = item;
        const subtotal = preco * quantidade;

        const itemCarrinho = document.createElement("div");
        itemCarrinho.innerHTML = `
            <h3>${nome}</h3>
            <p>Preço: R$ ${preco.toFixed(2)}</p>
            <p>Quantidade: ${quantidade}</p>
            <p>Subtotal: R$ ${subtotal.toFixed(2)}</p>
        `;

        const botaoRemover = document.createElement("button");
        botaoRemover.textContent = "Remover";
        botaoRemover.addEventListener("click", () => removerDoCarrinho(nome));
        itemCarrinho.appendChild(botaoRemover);

        areaCarrinho.appendChild(itemCarrinho);
    });

    areaTotal.innerHTML = `<strong>Total: R$ ${total.toFixed(2)}</strong>`;
}

// ===========================================================
// 15. VALIDAÇÃO DO FORMULÁRIO
// ===========================================================
const formulario = document.getElementById("formPedido");

formulario.addEventListener("submit", (evento) => {
    evento.preventDefault();

    const nome = document.getElementById("nome").value;
    const email = document.getElementById("email").value;

    if (nome === "") {
        alert("Digite seu nome!");
        return;
    }

    if (email === "") {
        alert("Digite seu e-mail!");
        return;
    }

    if (carrinho.length === 0) {
        alert("Adicione pelo menos um produto ao carrinho!");
        return;
    }

    alert("Pedido enviado com sucesso!");
    console.log("Nome do cliente:", nome);
    console.log("E-mail do cliente:", email);
    console.log("Itens do pedido:", carrinho);

    carrinho = [];
    mostrarCarrinho();
});

// ===========================================================
// 16. INICIAR O SISTEMA
// ===========================================================
mostrarCardapio();
mostrarCarrinho();
