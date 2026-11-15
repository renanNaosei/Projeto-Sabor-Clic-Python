/* Entidades do front-end (POO com campos privados #).
   Nenhuma delas acessa a API: só guardam estado e regras locais. */

export class Usuario {
  #id;
  #nome;
  #tipoUsuario;

  constructor({ id, nome, tipoUsuario }) {
    this.#id = id;
    this.#nome = nome;
    this.#tipoUsuario = tipoUsuario;
  }

  // Fábrica: devolve a subclasse certa (Cliente, Cozinheiro, Administrador) conforme o perfil da API.
  static deApi({ id, nome, tipo_usuario: tipoUsuario }) {
    const Perfil = PERFIS[tipoUsuario] ?? Usuario;
    return new Perfil({ id, nome, tipoUsuario });
  }

  get id() { return this.#id; }
  get nome() { return this.#nome; }
  get tipoUsuario() { return this.#tipoUsuario; }
  get isCliente() { return this.#tipoUsuario === "cliente"; }
  get isCozinheiro() { return this.#tipoUsuario === "cozinheiro"; }
  get isAdministrador() { return this.#tipoUsuario === "administrador"; }

  // Polimorfismo: por padrão ninguém pode nada; cada perfil sobrescreve o que lhe cabe.
  // (As regras valem também no servidor; aqui só decidem o que a tela mostra.)
  get podeFazerPedidos() { return false; }
  get podeVerFila() { return false; }
  get podeAtualizarStatus() { return false; }
}

export class Cliente extends Usuario {
  get podeFazerPedidos() { return true; }
}

export class Cozinheiro extends Usuario {
  get podeVerFila() { return true; }
  get podeAtualizarStatus() { return true; }
}

export class Administrador extends Usuario {
  get podeVerFila() { return true; } // acompanha a fila, mas quem muda o status é o cozinheiro
}

const PERFIS = { cliente: Cliente, cozinheiro: Cozinheiro, administrador: Administrador };

export class Prato {
  #id;
  #nome;
  #descricao;
  #preco;
  #categoria;
  #imagem;
  #ativo;

  constructor({ id, nome, descricao, preco, categoria, imagem, ativo }) {
    this.#id = id;
    this.#nome = nome;
    this.#descricao = descricao ?? "";
    this.#preco = Number(preco);
    this.#categoria = categoria ?? "Outros";
    this.#imagem = imagem ?? null;
    this.#ativo = Boolean(ativo);
  }

  static deApi(dados) {
    return new Prato(dados);
  }

  get id() { return this.#id; }
  get nome() { return this.#nome; }
  get descricao() { return this.#descricao; }
  get preco() { return this.#preco; }
  get categoria() { return this.#categoria; }
  get imagem() { return this.#imagem; }
  get ativo() { return this.#ativo; }
  get vegetariano() { return this.#categoria === "Vegetarianos"; }

  precoFormatado() {
    return this.#preco.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
}

export class ItemPedido {
  #prato;
  #quantidade;

  constructor(prato, quantidade = 1) {
    this.#prato = prato;
    this.#quantidade = quantidade;
  }

  get prato() { return this.#prato; }
  get quantidade() { return this.#quantidade; }

  alterar(variacao) {
    this.#quantidade += variacao;
  }

  subtotal() {
    return this.#prato.preco * this.#quantidade;
  }
}

export class Carrinho {
  #itens = [];

  get itens() {
    return [...this.#itens];
  }

  get vazio() {
    return this.#itens.length === 0;
  }

  get quantidadeTotal() {
    return this.#itens.reduce((soma, item) => soma + item.quantidade, 0);
  }

  adicionarPrato(prato) {
    const existente = this.#itens.find((item) => item.prato.id === prato.id);

    if (existente) {
      existente.alterar(1);
    } else {
      this.#itens.push(new ItemPedido(prato));
    }
  }

  alterarQuantidade(pratoId, variacao) {
    const item = this.#itens.find((i) => i.prato.id === pratoId);

    if (!item) return;

    item.alterar(variacao);

    if (item.quantidade < 1) {
      this.remover(pratoId);
    }
  }

  remover(pratoId) {
    this.#itens = this.#itens.filter((item) => item.prato.id !== pratoId);
  }

  limpar() {
    this.#itens = [];
  }

  total() {
    return this.#itens.reduce((acumulado, item) => acumulado + item.subtotal(), 0);
  }

  // Formato esperado pelo endpoint POST /api/pedidos (sem preços: quem define o preço é o servidor)
  paraPayload() {
    return this.#itens.map(({ prato, quantidade }) => ({
      prato_id: prato.id,
      quantidade,
    }));
  }

  // Versão mínima guardada no localStorage: só ids e quantidades.
  paraArmazenar() {
    return this.paraPayload();
  }

  // Reconstrói o carrinho a partir do que foi salvo. Pratos que saíram do
  // cardápio (removidos ou indisponíveis) são descartados.
  restaurar(salvos, pratosPorId) {
    this.#itens = [];

    if (!Array.isArray(salvos)) return;

    salvos.forEach(({ prato_id: pratoId, quantidade }) => {
      const prato = pratosPorId.get(pratoId);

      if (prato && Number.isInteger(quantidade) && quantidade > 0) {
        this.#itens.push(new ItemPedido(prato, quantidade));
      }
    });
  }
}

// Ordem em que um pedido avança na cozinha (igual às transições permitidas no servidor).
export const ETAPAS_PEDIDO = ["Aguardando", "Iniciando Preparo", "Em Preparo", "Pronto para Entrega"];

export class Pedido {
  #id;
  #status;
  #valorTotal;
  #itens;
  #observacoes;
  #dataHora;
  #clienteId;

  constructor({ id, status, valorTotal, itens = [], observacoes = null, dataHora = null, clienteId = null }) {
    this.#id = id;
    this.#status = status;
    this.#valorTotal = Number(valorTotal);
    this.#itens = itens;
    this.#observacoes = observacoes;
    const data = dataHora ? new Date(dataHora) : null;
    this.#dataHora = data && !Number.isNaN(data.getTime()) ? data : null;
    this.#clienteId = clienteId;
  }

  static deApi({
    id, status, valor_total: valorTotal, itens, observacoes,
    data_hora_pedido: dataHora, cliente_id: clienteId,
  }) {
    return new Pedido({ id, status, valorTotal, itens, observacoes, dataHora, clienteId });
  }

  get id() { return this.#id; }
  get status() { return this.#status; }
  get valorTotal() { return this.#valorTotal; }
  get itens() { return [...this.#itens]; }
  get observacoes() { return this.#observacoes; }
  get dataHora() { return this.#dataHora; }
  get clienteId() { return this.#clienteId; }

  // Posição do status na ordem da cozinha (0 a 3).
  get etapa() { return Math.max(0, ETAPAS_PEDIDO.indexOf(this.#status)); }
  get finalizado() { return this.#status === ETAPAS_PEDIDO.at(-1); }
  get proximoStatus() { return this.finalizado ? null : ETAPAS_PEDIDO[this.etapa + 1]; }
  get totalItens() { return this.#itens.reduce((soma, item) => soma + Number(item.quantidade), 0); }

  minutosDesdeOPedido(agora = Date.now()) {
    return this.#dataHora ? Math.max(0, Math.floor((agora - this.#dataHora.getTime()) / 60000)) : null;
  }
}
