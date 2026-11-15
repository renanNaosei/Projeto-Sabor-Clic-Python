import { Carrinho, ETAPAS_PEDIDO, Pedido, Prato, Usuario } from "./models.js";
import { Api, ApiError } from "./api.js";
import { $, aviso, carregando, carregarTemaSalvo, criar, iniciarBotoesDeTema, moeda, normalizar } from "./ui.js";

const CHAVE_CARRINHO = "sabor_clic_carrinho_v1";
// A ordem das chaves é a ordem das categorias na tela; as não listadas vão para o fim.
const ICONES = {
  Lanches: "🍔", Vegetarianos: "🥬", Pizzas: "🍕", Massas: "🍝", Porções: "🍟", Saladas: "🥗",
  Sobremesas: "🍰", Bebidas: "🥤", Marmitas: "🍱", "Pratos principais": "🍽️",
};
const ORDEM = Object.keys(ICONES);
const icone = (categoria) => ICONES[categoria] ?? "🍽️";

const carrinho = new Carrinho();
let pratos = new Map(); // pratos da API, indexados pelo id
let usuario = null;
let categoriaAtiva = "Todas";
let focoAnterior = null;
let temporizadorPaineis = null;
let atualizandoPaineis = false;
let repetirAtualizacao = false;

const INTERVALO_ATUALIZACAO_MS = 10000; // fila e "meus pedidos" são reconsultados a cada 10 s, sem F5
// Texto do botão da cozinha para levar o pedido ao próximo status.
const ACAO_STATUS = {
  "Iniciando Preparo": "▶ Iniciar preparo",
  "Em Preparo": "🍳 Colocar em preparo",
  "Pronto para Entrega": "✅ Marcar como pronto",
};

/* ===================== Utilidades ===================== */

const mostrarErro = (erro, padrao) => aviso(erro instanceof ApiError ? erro.message : padrao, "erro");

function botao(classe, texto, acao, rotulo) {
  const el = criar("button", { classe, texto, atributos: { type: "button", ...(rotulo && { "aria-label": rotulo }) } });
  el.addEventListener("click", acao);
  return el;
}

// Flash Messages do servidor: a API entrega cada mensagem uma única vez.
async function mostrarMensagens(exibir = true) {
  try {
    const mensagens = await Api.consumirMensagens();
    if (exibir) mensagens.forEach(({ texto, categoria }) => aviso(texto, categoria === "erro" ? "erro" : "info"));
  } catch { /* sem flash messages não é erro de uso */ }
}

/* ===================== Carrinho ===================== */

function atualizarCarrinho() {
  try { localStorage.setItem(CHAVE_CARRINHO, JSON.stringify(carrinho.paraArmazenar())); } catch { /* armazenamento bloqueado */ }
  desenharCarrinho();
}

function lerCarrinhoSalvo() {
  try { return JSON.parse(localStorage.getItem(CHAVE_CARRINHO)) ?? []; } catch { return []; }
}

function desenharCarrinho() {
  const area = $("cartItems");
  area.replaceChildren();

  if (carrinho.vazio) {
    area.append(criar("div", { classe: "empty-cart", texto: "Seu carrinho está vazio. Escolha algo gostoso no cardápio!" }));
  }

  carrinho.itens.forEach((item) => {
    const { prato, quantidade } = item;
    const mudar = (variacao) => () => { carrinho.alterarQuantidade(prato.id, variacao); atualizarCarrinho(); };

    const controles = criar("div", { classe: "cart-controls" },
      botao("qty-btn", "−", mudar(-1), `Diminuir quantidade de ${prato.nome}`),
      criar("span", { texto: quantidade }),
      botao("qty-btn", "+", mudar(1), `Aumentar quantidade de ${prato.nome}`),
      botao("remove-btn", "Remover", () => { carrinho.remover(prato.id); atualizarCarrinho(); }),
    );

    area.append(criar("div", { classe: "cart-item" },
      criar("div", {}, criar("h3", { texto: prato.nome }), criar("small", { texto: `${moeda(prato.preco)} cada` }), controles),
      criar("strong", { texto: moeda(item.subtotal()) }),
    ));
  });

  $("counter").textContent = carrinho.quantidadeTotal;
  $("total").textContent = moeda(carrinho.total());
}

function adicionarAoCarrinho(prato, el) {
  carrinho.adicionarPrato(prato);
  atualizarCarrinho();
  aviso(`${prato.nome} adicionado!`);

  const pilula = $("goCart");
  pilula.classList.remove("bump");
  void pilula.offsetWidth; // reinicia a animação
  pilula.classList.add("bump");

  el.dataset.label ??= el.textContent;
  el.textContent = "✓ Adicionado";
  el.classList.add("added");
  clearTimeout(el.temporizador);
  el.temporizador = setTimeout(() => { el.textContent = el.dataset.label; el.classList.remove("added"); }, 900);
}

/* ===================== Cardápio ===================== */

function criarFoto(prato) {
  const foto = criar("div", { classe: "product-photo" });
  const semImagem = (texto) => {
    foto.classList.add("photo-fallback");
    foto.append(criar("span", { texto }));
  };

  // Só aceita URLs http(s) vindas do banco.
  if (/^https?:\/\//i.test(prato.imagem ?? "")) {
    const img = criar("img", { atributos: { src: prato.imagem, alt: `Foto ilustrativa de ${prato.nome}`, loading: "lazy" } });
    img.addEventListener("error", () => { img.remove(); semImagem("Imagem indisponível"); }, { once: true });
    foto.append(img);
  } else {
    semImagem(prato.nome);
  }

  foto.append(criar("span", { classe: "product-tag", texto: prato.categoria }));
  if (prato.vegetariano) foto.append(criar("span", { classe: "product-seal veg", texto: "🌱 Vegetariano" }));
  return foto;
}

function criarCard(prato) {
  const add = botao("add-btn", "＋ Adicionar", () => adicionarAoCarrinho(prato, add), `Adicionar ${prato.nome}`);

  const card = criar("article", { classe: "product" },
    criarFoto(prato),
    criar("div", { classe: "product-body" },
      criar("div", {}, criar("h3", { texto: prato.nome }), criar("p", { classe: "product-desc", texto: prato.descricao })),
      criar("div", { classe: "product-bottom" }, criar("span", { classe: "price", texto: prato.precoFormatado() }), add),
    ),
  );

  card.dataset.category = prato.categoria;
  card.dataset.search = normalizar(`${prato.nome} ${prato.categoria} ${prato.descricao}`);
  return card;
}

function desenharCardapio(lista) {
  const posicao = (c) => (ORDEM.includes(c) ? ORDEM.indexOf(c) : ORDEM.length);
  const categorias = [...new Set(lista.map((p) => p.categoria))]
    .sort((a, b) => posicao(a) - posicao(b) || a.localeCompare(b, "pt-BR"));

  const nav = $("categoryNav");
  nav.replaceChildren(...["Todas", ...categorias].map((c) => {
    const chip = botao("chip", c === "Todas" ? "✨ Tudo" : `${icone(c)} ${c}`, () => irParaCategoria(c));
    chip.dataset.catFilter = c;
    return chip;
  }));

  $("menuRoot").replaceChildren(...categorias.map((c) => {
    const secao = criar("section", { classe: "category-section" },
      criar("div", { classe: "section-heading" }, criar("h2", { texto: `${icone(c)} ${c}` })),
      criar("div", { classe: "product-grid" }, ...lista.filter((p) => p.categoria === c).map(criarCard)),
    );
    secao.dataset.categorySection = c;
    return secao;
  }));

  marcarChip(categoriaAtiva);
  filtrar();
}

function mostrarEstado(texto, comTentarNovamente = false) {
  $("menuRoot").replaceChildren(criar("p", { classe: "menu-estado", texto }));
  if (comTentarNovamente) $("menuRoot").append(botao("add-btn", "Tentar novamente", carregarCardapio));
  $("resultCount").textContent = "—";
}

async function carregarCardapio() {
  $("menuRoot").setAttribute("aria-busy", "true");
  mostrarEstado("Carregando cardápio…");

  try {
    const lista = (await Api.listarCardapio(true)).map(Prato.deApi);
    pratos = new Map(lista.map((p) => [p.id, p]));
    carrinho.restaurar(lerCarrinhoSalvo(), pratos); // descarta pratos que saíram do cardápio
    atualizarCarrinho();

    if (lista.length) desenharCardapio(lista);
    else mostrarEstado("Nenhum prato disponível no momento.");
  } catch (erro) {
    mostrarEstado(erro instanceof ApiError ? erro.message : "Erro ao carregar o cardápio.", true);
    mostrarErro(erro, "Erro ao carregar o cardápio.");
  } finally {
    $("menuRoot").setAttribute("aria-busy", "false");
  }
}

/* ===================== Busca e filtro ===================== */

function filtrar() {
  const termo = normalizar($("search").value.trim());
  let total = 0;

  document.querySelectorAll(".product").forEach((card) => {
    const visivel = (categoriaAtiva === "Todas" || card.dataset.category === categoriaAtiva)
      && (!termo || card.dataset.search.includes(termo));
    card.hidden = !visivel;
    if (visivel) total += 1;
  });

  document.querySelectorAll(".category-section").forEach((secao) => {
    secao.hidden = !secao.querySelector(".product:not([hidden])");
  });

  $("emptyResults").hidden = total > 0 || pratos.size === 0;
  $("resultCount").textContent = `${total} ${total === 1 ? "produto encontrado" : "produtos encontrados"}`;
}

function marcarChip(categoria) {
  document.querySelectorAll("[data-cat-filter]").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.catFilter === categoria);
  });
}

function definirCategoria(categoria) {
  categoriaAtiva = categoria;
  marcarChip(categoria);
  filtrar();
}

// Clicar numa categoria mostra o cardápio completo e rola até ela.
function irParaCategoria(categoria) {
  $("search").value = "";
  definirCategoria("Todas");
  marcarChip(categoria);

  const alvo = categoria === "Todas"
    ? $("cardapio")
    : document.querySelector(`[data-category-section="${CSS.escape(categoria)}"]`);
  alvo?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function limparBusca() {
  $("search").value = "";
  definirCategoria("Todas");
}

// Ao pesquisar, leva a barra de busca para perto do topo para os resultados ficarem visíveis.
function mostrarResultadosBusca() {
  const topo = document.querySelector("header").offsetHeight;
  const { top } = document.querySelector(".toolbar").getBoundingClientRect();
  if (top > topo + 20 || top < 0) window.scrollTo({ top: window.scrollY + top - topo - 10, behavior: "smooth" });
}

/* ===================== Conta (login, cadastro, sessão) ===================== */

async function atualizarConta() {
  try {
    const dados = await Api.usuarioAtual();
    usuario = dados ? Usuario.deApi(dados) : null;
  } catch {
    usuario = null;
  }

  const logado = usuario !== null;
  const podePedir = logado && usuario.podeFazerPedidos;

  $("usuarioLogado").hidden = !logado;
  $("usuarioLogado").textContent = logado ? `👤 ${usuario.nome}` : "";
  $("botaoLogout").hidden = !logado;
  $("formLogin").hidden = logado;
  if (logado) $("formCadastro").hidden = true;
  $("alternarConta").hidden = logado;
  $("checkoutForm").hidden = !podePedir;
  $("avisoPerfil").hidden = !logado || podePedir;
  $("avisoPerfil").textContent = logado && !podePedir
    ? usuario.podeVerFila
      ? `Conta de ${usuario.tipoUsuario}: não faz pedidos. Acompanhe a fila da cozinha logo abaixo.`
      : `Contas do tipo "${usuario.tipoUsuario}" não fazem pedidos. Saia e entre com uma conta de cliente.`
    : "";
  $("checkoutSub").textContent = podePedir
    ? `Pedido em nome de ${usuario.nome}.`
    : logado ? "Esta conta não pode fazer pedidos." : "Entre na sua conta para finalizar o pedido.";

  await atualizarPaineis();
}

function alternarCadastro(mostrar) {
  $("formLogin").hidden = mostrar;
  $("formCadastro").hidden = !mostrar;
  $("linkCadastro").hidden = mostrar;
  $("linkLogin").hidden = !mostrar;
}

// Login e cadastro seguem o mesmo roteiro: botão ocupado -> ação -> atualiza a conta -> mensagens do servidor.
async function enviarFormulario(evento, idBotao, rotulo, acao, erroPadrao) {
  evento.preventDefault();
  const el = $(idBotao);
  carregando(el, true, rotulo);

  try {
    await acao();
    await atualizarConta();
    await mostrarMensagens();
  } catch (erro) {
    mostrarErro(erro, erroPadrao);
  } finally {
    carregando(el, false);
  }
}

const entrar = (evento) => enviarFormulario(evento, "botaoLogin", "Entrando…", async () => {
  await Api.login($("email").value.trim(), $("senha").value);
  $("formLogin").reset();
}, "Erro ao entrar.");

const cadastrar = (evento) => enviarFormulario(evento, "botaoCadastro", "Cadastrando…", async () => {
  const email = $("cadEmail").value.trim();
  const senha = $("cadSenha").value;
  await Api.cadastrar({ nome: $("cadNome").value.trim(), email, senha });
  await Api.login(email, senha); // já entra logado após o cadastro
  $("formCadastro").reset();
  alternarCadastro(false);
}, "Erro ao cadastrar.");

async function sair() {
  try {
    await Api.logout();
  } catch (erro) {
    mostrarErro(erro, "Erro ao sair.");
  } finally {
    await atualizarConta();
    await mostrarMensagens();
  }
}

/* ===================== Pedidos: "meus pedidos" (cliente) e fila (cozinha) ===================== */

const hora = (data) => data?.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) ?? "";
const horaCompleta = () => new Date().toLocaleTimeString("pt-BR");

function nomeDoItem({ nome, prato_id: id }) {
  return nome ?? pratos.get(id)?.nome ?? `Prato #${id}`;
}

function desenharEtapas(pedido) {
  return criar("div", { classe: "etapas", atributos: { role: "img", "aria-label": `Etapa ${pedido.etapa + 1} de ${ETAPAS_PEDIDO.length}: ${pedido.status}` } },
    ...ETAPAS_PEDIDO.map((_, indice) => criar("span", { classe: indice <= pedido.etapa ? "etapa feita" : "etapa" })));
}

// Parte comum dos dois painéis: número, hora, status, itens, observações e total.
function desenharCartaoPedido(pedido, rotuloTopo) {
  const cartao = criar("article", { classe: "pedido-card" },
    criar("div", { classe: "pedido-topo" },
      criar("strong", { texto: rotuloTopo }),
      criar("span", { classe: "pedido-hora", texto: hora(pedido.dataHora) })),
    criar("span", { classe: `status-selo etapa-${pedido.etapa}`, texto: pedido.status }),
    desenharEtapas(pedido),
    criar("ul", { classe: "pedido-itens" }, ...pedido.itens.map((item) =>
      criar("li", { texto: `${item.quantidade}x ${nomeDoItem(item)}` }))));

  if (pedido.observacoes) cartao.append(criar("p", { classe: "pedido-obs", texto: `Obs.: ${pedido.observacoes}` }));
  return cartao;
}

function mostrarVazio(lista, texto) {
  lista.replaceChildren(criar("div", { classe: "pedido-vazio", texto }));
}

async function carregarMeusPedidos() {
  const pedidos = (await Api.listarMeusPedidos()).map((dados) => Pedido.deApi(dados));

  if (pedidos.length === 0) {
    mostrarVazio($("listaMeusPedidos"), "Você ainda não fez pedidos.");
  } else {
    $("listaMeusPedidos").replaceChildren(...pedidos.map((pedido) => {
      const cartao = desenharCartaoPedido(pedido, `Pedido #${pedido.id}`);
      cartao.append(criar("div", { classe: "pedido-rodape" }, criar("span", { texto: "Total" }), criar("strong", { texto: moeda(pedido.valorTotal) })));
      return cartao;
    }));
  }

  $("subMeusPedidos").textContent = `Atualizado às ${horaCompleta()}. A lista atualiza sozinha a cada ${INTERVALO_ATUALIZACAO_MS / 1000} s.`;
}

function desenharCartaoFila(pedido) {
  const minutos = pedido.minutosDesdeOPedido();
  const cartao = desenharCartaoPedido(pedido, `Pedido #${pedido.id} • Cliente #${pedido.clienteId}`);

  cartao.append(criar("div", { classe: "pedido-rodape" },
    criar("span", { texto: minutos === null ? "" : `há ${minutos} min` }),
    criar("strong", { texto: moeda(pedido.valorTotal) })));

  if (usuario.podeAtualizarStatus && pedido.proximoStatus) {
    const avancar = botao("add-btn", ACAO_STATUS[pedido.proximoStatus], () => avancarStatus(pedido, avancar));
    cartao.append(avancar);
  }

  return cartao;
}

async function carregarFila() {
  const pedidos = (await Api.listarPedidos()).map((dados) => Pedido.deApi(dados));
  const emAndamento = pedidos.filter((pedido) => !pedido.finalizado);
  const prontos = pedidos.filter((pedido) => pedido.finalizado).slice(-6).reverse();

  if (emAndamento.length === 0) mostrarVazio($("listaFila"), "Nenhum pedido na fila. 🎉");
  else $("listaFila").replaceChildren(...emAndamento.map(desenharCartaoFila));

  $("tituloProntos").hidden = prontos.length === 0;
  $("listaProntos").replaceChildren(...prontos.map(desenharCartaoFila));
  $("subFila").textContent = `${emAndamento.length} ${emAndamento.length === 1 ? "pedido em andamento" : "pedidos em andamento"}. `
    + `Atualizado às ${horaCompleta()} (a cada ${INTERVALO_ATUALIZACAO_MS / 1000} s).`;
}

async function avancarStatus(pedido, el) {
  carregando(el, true, "Atualizando…");

  try {
    await Api.atualizarStatusPedido(pedido.id, pedido.proximoStatus);
    aviso(`Pedido #${pedido.id}: ${pedido.proximoStatus}.`);
    await carregarFila();
  } catch (erro) {
    mostrarErro(erro, "Erro ao atualizar o status.");
    if (erro instanceof ApiError && (erro.status === 401 || erro.status === 403)) await atualizarConta();
    else await carregarFila().catch(() => {}); // outro cozinheiro pode ter mexido no pedido
  } finally {
    // o cartão antigo já foi substituído; só desfaz o estado se o botão ainda estiver na tela
    if (el.isConnected) carregando(el, false);
  }
}

// Mostra o painel que cabe ao perfil logado e o preenche. Falhas de rede não geram aviso a cada 10 s.
async function atualizarPaineis() {
  const verMeus = usuario?.podeFazerPedidos === true;
  const verFila = usuario?.podeVerFila === true;

  $("painelMeusPedidos").hidden = !verMeus;
  $("painelFila").hidden = !verFila;
  if (!verMeus && !verFila) return;

  if (atualizandoPaineis) { // já há uma consulta em andamento: repete logo depois, com o estado mais novo
    repetirAtualizacao = true;
    return;
  }

  atualizandoPaineis = true;
  let sessaoExpirou = false;

  try {
    if (verMeus) await carregarMeusPedidos();
    if (verFila) await carregarFila();
  } catch (erro) {
    sessaoExpirou = erro instanceof ApiError && erro.status === 401;
    const texto = erro instanceof ApiError && erro.status === 0
      ? "Sem conexão com a API. Tentando de novo em instantes…"
      : "Não foi possível atualizar agora.";
    $(verMeus ? "subMeusPedidos" : "subFila").textContent = texto;
  } finally {
    atualizandoPaineis = false;
  }

  if (sessaoExpirou) await atualizarConta(); // a sessão caiu: reconfere quem está logado
  else if (repetirAtualizacao) {
    repetirAtualizacao = false;
    await atualizarPaineis();
  }
}

function iniciarAtualizacaoAutomatica() {
  clearInterval(temporizadorPaineis);
  temporizadorPaineis = setInterval(() => {
    if (!document.hidden) atualizarPaineis();
  }, INTERVALO_ATUALIZACAO_MS);

  // Ao voltar para a aba, atualiza na hora em vez de esperar o próximo ciclo.
  document.addEventListener("visibilitychange", () => { if (!document.hidden) atualizarPaineis(); });
}

/* ===================== Finalização do pedido ===================== */

function abrirModal(pedido) {
  $("modalOrderNumber").textContent = `Pedido #${pedido.id} • ${pedido.status}`;
  $("modalGreeting").textContent = `Obrigado, ${usuario?.nome ?? "cliente"}! Seu pedido foi registrado.`;

  const lista = criar("ul", {}, ...pedido.itens.map(({ nome, prato_id: id, quantidade, subtotal }) =>
    criar("li", { texto: `${quantidade}x ${nome ?? pratos.get(id)?.nome ?? `Prato #${id}`} — ${moeda(Number(subtotal))}` })));

  $("modalSummary").replaceChildren(criar("strong", { texto: "Resumo do pedido:" }), lista);
  if (pedido.observacoes) {
    $("modalSummary").append(criar("div", { classe: "modal-obs", texto: `Observações: "${pedido.observacoes}"` }));
  }
  $("modalSummary").append(criar("div", { classe: "modal-total" }, criar("span", { texto: "Total" }), criar("span", { texto: moeda(pedido.valorTotal) })));

  focoAnterior = document.activeElement;
  $("orderModal").classList.add("open");
  $("closeModalBtn").focus();
}

function fecharModal() {
  $("orderModal").classList.remove("open");
  focoAnterior?.focus();
}

async function finalizarPedido(evento) {
  evento.preventDefault();

  if (carrinho.vazio) {
    aviso("Adicione pelo menos um produto antes de finalizar.", "erro");
    $("cardapio").scrollIntoView({ behavior: "smooth" });
    return;
  }

  const el = $("botaoPedido");
  carregando(el, true, "Enviando pedido…");

  try {
    const pedido = Pedido.deApi(await Api.criarPedido(carrinho.paraPayload(), $("customerNotes").value.trim()));
    carrinho.limpar();
    atualizarCarrinho();
    $("checkoutForm").reset();
    abrirModal(pedido);
    await mostrarMensagens(false); // esvazia a fila de flash; o modal já confirma o pedido
    await atualizarPaineis();
  } catch (erro) {
    mostrarErro(erro, "Erro ao enviar o pedido.");
    if (erro instanceof ApiError && erro.status === 401) await atualizarConta(); // sessão expirou
    if (erro instanceof ApiError && erro.status === 409) await carregarCardapio(); // prato removido ou sem estoque
  } finally {
    carregando(el, false);
  }
}

/* ===================== Inicialização ===================== */

carregarTemaSalvo();
iniciarBotoesDeTema();

$("search").addEventListener("input", () => {
  definirCategoria("Todas");
  if ($("search").value.trim()) mostrarResultadosBusca();
});
$("clearSearch").addEventListener("click", limparBusca);
$("resetFiltersBtn").addEventListener("click", limparBusca);
$("goCart").addEventListener("click", () => $("pedido").scrollIntoView({ behavior: "smooth" }));
$("formLogin").addEventListener("submit", entrar);
$("formCadastro").addEventListener("submit", cadastrar);
$("linkCadastro").addEventListener("click", () => alternarCadastro(true));
$("linkLogin").addEventListener("click", () => alternarCadastro(false));
$("botaoLogout").addEventListener("click", sair);
$("checkoutForm").addEventListener("submit", finalizarPedido);
$("closeModalBtn").addEventListener("click", fecharModal);
$("orderModal").addEventListener("click", (evento) => { if (evento.target === $("orderModal")) fecharModal(); });
document.addEventListener("keydown", (evento) => {
  if (!$("orderModal").classList.contains("open")) return;
  if (evento.key === "Escape") fecharModal();
  if (evento.key === "Tab") evento.preventDefault(); // único elemento focável do modal
});

desenharCarrinho();
iniciarAtualizacaoAutomatica();
await Promise.all([carregarCardapio(), atualizarConta()]);