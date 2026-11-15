// Mesmo host (127.0.0.1) do front, para o cookie de sessão trafegar (SameSite=Lax).
const BASE_URL = "http://127.0.0.1:5000/api";
const METODOS_SEGUROS = new Set(["GET", "HEAD", "OPTIONS"]);

export class ApiError extends Error {
  constructor(mensagem, status, codigo = null) {
    super(mensagem);
    this.name = "ApiError";
    this.status = status;
    this.codigo = codigo;
  }
}

// Token anti-CSRF: guardado só em memória (a cada recarga é pedido de novo ao servidor).
let tokenCsrf = null;

function montarMensagem(corpo) {
  const base = corpo?.erro ?? "Erro desconhecido";
  const detalhes = corpo?.detalhes;

  if (Array.isArray(detalhes) && detalhes.length > 0) {
    return `${base} ${detalhes.join(" ")}`;
  }

  return base;
}

async function enviar(caminho, opcoes, tentarDeNovo) {
  const metodo = (opcoes.method ?? "GET").toUpperCase();
  const headers = { "Content-Type": "application/json", ...(opcoes.headers ?? {}) };

  if (!METODOS_SEGUROS.has(metodo)) {
    headers["X-CSRF-Token"] = tokenCsrf ?? (await obterTokenCsrf());
  }

  let resposta;

  try {
    resposta = await fetch(`${BASE_URL}${caminho}`, { ...opcoes, headers, credentials: "include" });
  } catch {
    throw new ApiError("Não foi possível conectar à API", 0);
  }

  const corpo = await resposta.json().catch(() => null);

  if (!resposta.ok || !corpo?.sucesso) {
    // Token expirado ou sessão trocada: busca outro e repete uma única vez.
    if (corpo?.codigo === "CSRF_INVALIDO" && tentarDeNovo) {
      tokenCsrf = null;
      return enviar(caminho, opcoes, false);
    }

    throw new ApiError(montarMensagem(corpo), resposta.status, corpo?.codigo ?? null);
  }

  return corpo;
}

async function obterTokenCsrf() {
  const resposta = await enviar("/auth/csrf", {}, false);
  tokenCsrf = resposta.csrf_token;
  return tokenCsrf;
}

// Devolve só o campo "dados" da resposta padrão { sucesso, dados }.
async function requisitar(caminho, opcoes = {}) {
  return (await enviar(caminho, opcoes, true)).dados;
}

export const Api = {
  listarCardapio(apenasAtivos = true) {
    return requisitar(`/menu?ativo=${apenasAtivos}`);
  },

  // O cliente é identificado pela sessão; o corpo leva só itens e observações.
  criarPedido(itens, observacoes = "") {
    return requisitar("/pedidos", {
      method: "POST",
      body: JSON.stringify({ itens, observacoes }),
    });
  },

  // Fila da cozinha: todos os pedidos (somente cozinheiro e administrador).
  listarPedidos() {
    return requisitar("/pedidos");
  },

  // Pedidos do cliente logado.
  listarMeusPedidos() {
    return requisitar("/pedidos/meus");
  },

  atualizarStatusPedido(pedidoId, status) {
    return requisitar(`/pedidos/${pedidoId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },

  cadastrar({ nome, email, senha }) {
    return requisitar("/auth/register", {
      method: "POST",
      body: JSON.stringify({ nome, email, senha }),
    });
  },

  async login(email, senha) {
    const resposta = await enviar("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, senha }),
    }, true);

    tokenCsrf = resposta.csrf_token; // o login troca a sessão e gera um token novo
    return resposta.dados;
  },

  async logout() {
    try {
      return await requisitar("/auth/logout", { method: "POST" });
    } finally {
      tokenCsrf = null;
    }
  },

  // Sem sessão a API responde 200 com dados = null.
  usuarioAtual() {
    return requisitar("/auth/me");
  },

  consumirMensagens() {
    return requisitar("/mensagens");
  },
};
