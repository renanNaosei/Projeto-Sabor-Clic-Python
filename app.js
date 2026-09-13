async function carregarMenu() {

    const status =
        document.querySelector("#status");

    const menu =
        document.querySelector("#menu");


    try {

        status.textContent =
            "Carregando cardápio...";


        const resposta =
            await buscarMenu();


        menu.innerHTML =
            resposta.dados
                .map(prato => `
                    <article>

                        <h2>
                            ${prato.nome}
                        </h2>

                        <p>
                            ${prato.descricao}
                        </p>

                        <strong>
                            R$ ${prato.preco
                                .toFixed(2)
                                .replace(".", ",")}
                        </strong>

                    </article>
                `)
                .join("");


        status.textContent =
            `${resposta.dados.length} prato(s) disponível(is).`;


    } catch (erro) {

        status.textContent =
            `Erro: ${erro.message}`;

    }
}


carregarMenu();