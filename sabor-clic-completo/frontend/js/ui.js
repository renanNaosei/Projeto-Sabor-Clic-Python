/* Utilidades de interface: criação segura de elementos, avisos, tema e formatação. */

const CHAVE_TEMA = "sabor_clic_tema_v1";

export const $ = (id) => document.getElementById(id);

export const moeda = (valor) =>
  Number(valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

// Remove acentos e caixa para a busca ("pizza" encontra "Pizzá").
export const normalizar = (texto) =>
  String(texto).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

// Cria elementos usando textContent (nunca innerHTML), evitando XSS com dados vindos da API.
export function criar(tag, { classe, texto, atributos = {} } = {}, ...filhos) {
  const elemento = document.createElement(tag);

  if (classe) elemento.className = classe;
  if (texto !== undefined) elemento.textContent = texto;

  Object.entries(atributos).forEach(([nome, valor]) => elemento.setAttribute(nome, valor));
  elemento.append(...filhos);

  return elemento;
}

let temporizadorAviso = null;

export function aviso(texto, tipo = "info") {
  const toast = $("toast");

  toast.textContent = texto;
  toast.classList.toggle("erro", tipo === "erro");
  toast.classList.add("show");

  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => toast.classList.remove("show"), tipo === "erro" ? 4000 : 2200);
}

// Estado de carregamento de um botão: desabilita e troca o texto enquanto a requisição roda.
export function carregando(botao, ativo, textoEnquanto = "Aguarde…") {
  if (ativo) {
    botao.dataset.textoOriginal = botao.textContent;
    botao.textContent = textoEnquanto;
  } else if (botao.dataset.textoOriginal) {
    botao.textContent = botao.dataset.textoOriginal;
  }

  botao.disabled = ativo;
}

/* ---- Tema (claro / escuro / alto contraste) ---- */

export function aplicarTema(tema, salvar = true) {
  if (tema !== "dark-mode" && tema !== "high-contrast") tema = "";

  [document.documentElement, document.body].forEach((el) => {
    el.classList.toggle("dark-mode", tema === "dark-mode");
    el.classList.toggle("high-contrast", tema === "high-contrast");
  });

  const botaoEscuro = $("darkMode");
  const botaoContraste = $("highContrast");

  botaoEscuro.setAttribute("aria-pressed", String(tema === "dark-mode"));
  botaoEscuro.textContent = tema === "dark-mode" ? "☀️ Modo claro" : "🌙 Modo escuro";
  botaoContraste.setAttribute("aria-pressed", String(tema === "high-contrast"));
  botaoContraste.textContent = tema === "high-contrast" ? "◐ Contraste normal" : "◐ Alto contraste";
  document.documentElement.dataset.theme = tema || "light";

  if (salvar) {
    try { localStorage.setItem(CHAVE_TEMA, tema); } catch { /* armazenamento bloqueado */ }
  }
}

export function carregarTemaSalvo() {
  try {
    aplicarTema(localStorage.getItem(CHAVE_TEMA) || "", false);
  } catch {
    aplicarTema("", false);
  }
}

export function iniciarBotoesDeTema() {
  $("darkMode").addEventListener("click", () => {
    aplicarTema(document.body.classList.contains("dark-mode") ? "" : "dark-mode");
  });

  $("highContrast").addEventListener("click", () => {
    aplicarTema(document.body.classList.contains("high-contrast") ? "" : "high-contrast");
  });
}
