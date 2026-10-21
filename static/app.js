async function enviar(rota, corpo) {
  const resposta = await fetch(rota, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  if (!resposta.ok) throw new Error("Erro " + resposta.status);
  return resposta.json();
}

// Cria um elemento com classe e texto. O texto entra sempre por textContent,
// nunca por innerHTML, para que nada digitado vire código na página.
function el(tag, classe, texto) {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

const espera = (ms) => new Promise((r) => setTimeout(r, ms));
const preco = (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

function aviso(texto) {
  const t = el("div", "toast", texto);
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2200);
}

// Ícone só para facilitar a leitura; não muda nada na busca.
const EMOJIS = [
  [/sabonete|sab[aã]o|saponáceo/i, "🧼"],
  [/piscina/i, "🏊"],
  [/vidro/i, "🪟"],
  [/cera|lustra|pedra|piso/i, "🧹"],
  [/álcool|alcool|gel/i, "🫧"],
  [/odorizador/i, "🌸"],
  [/amaciante|roupa|alvejante/i, "👕"],
];
const emoji = (nome) => (EMOJIS.find(([re]) => re.test(nome)) || [null, "🧴"])[1];

// Catálogo carregado uma vez para montar os cartões de produto.
let catalogo = [];
const porCodigo = new Map();

async function carregarCatalogo() {
  try {
    const r = await fetch("/itens");
    catalogo = await r.json();
  } catch {
    catalogo = [];
  }
  catalogo.forEach((i) => porCodigo.set(i.codigo, i));
  desenharCatalogo();
}

function cartaoProduto(item, comAcoes) {
  const c = el("div", "produto");
  const topo = el("div", "produto-topo");
  topo.append(el("span", "produto-emoji", emoji(item.nome)), el("span", "produto-nome", item.nome));
  const rodape = el("div", "produto-rodape");
  rodape.append(el("span", "preco", preco(item.preco)), el("span", "codigo", item.codigo));
  c.append(topo, el("span", "produto-desc", item.descricao), el("span", "etiqueta", item.unidade), rodape);
  c.querySelector(".etiqueta").style.alignSelf = "flex-start";
  if (comAcoes) {
    const acoes = el("div", "produto-acoes");
    const perguntar = el("button", "", "Perguntar no chat");
    perguntar.type = "button";
    perguntar.addEventListener("click", () => {
      trocarAba("chat");
      perguntarAoCheek(`Quanto custa ${item.nome}?`);
    });
    const conferir = el("button", "", "Conferir");
    conferir.type = "button";
    conferir.addEventListener("click", () => {
      trocarAba("conferencia");
      conferirItem(item.nome);
    });
    acoes.append(perguntar, conferir);
    c.append(acoes);
  }
  return c;
}

// Abas
function trocarAba(nome) {
  document.querySelectorAll(".aba").forEach((b) => {
    const ativa = b.dataset.aba === nome;
    b.classList.toggle("ativa", ativa);
    b.setAttribute("aria-selected", ativa);
  });
  document.querySelectorAll(".painel").forEach((p) => p.classList.toggle("ativo", p.id === nome));
}
document.querySelectorAll(".aba").forEach((b) => b.addEventListener("click", () => trocarAba(b.dataset.aba)));

// Ajuda: aparece sozinha na primeira visita.
const ajuda = document.getElementById("ajuda");
document.getElementById("abrir-ajuda").addEventListener("click", () => ajuda.showModal());
try {
  if (!localStorage.getItem("cheek-ajuda-vista")) {
    ajuda.showModal();
    localStorage.setItem("cheek-ajuda-vista", "1");
  }
} catch {
  // Sem armazenamento local a ajuda continua disponível pelo botão.
}

// Chat
const caixa = document.getElementById("mensagens");

function linhaMensagem(lado) {
  const linha = el("div", "linha " + lado);
  if (lado === "cheek") linha.append(el("span", "avatar", "C"));
  caixa.appendChild(linha);
  return linha;
}

function rolar() {
  caixa.scrollTop = caixa.scrollHeight;
}

function mensagemCliente(texto) {
  linhaMensagem("cliente").append(el("div", "balao", texto));
  rolar();
}

function mensagemCheek(r) {
  const balao = el("div", "balao");
  if (r.recusou) {
    const seguranca = r.resposta.startsWith("Por segurança");
    balao.classList.add(seguranca ? "seguranca" : "recusa");
    balao.append(el("div", "titulo-balao", seguranca ? "⚠️ Assunto de segurança" : "🤔 Não sei responder isso"));
    balao.append(el("div", "", r.resposta));
    balao.append(el("div", "explicacao", seguranca
      ? "Para produto químico, a orientação certa está no rótulo e na ficha de segurança (FISPQ)."
      : "O Cheek só responde com o que está no catálogo. Assim ele não inventa produto nem preço."));
  } else {
    // A resposta lista os itens em linhas que começam com "- ". Eles viram cartões;
    // as outras linhas aparecem como texto.
    const linhas = r.resposta.split("\n");
    const textos = linhas.filter((l) => !l.startsWith("- "));
    const itens = r.itens.map((c) => porCodigo.get(c)).filter(Boolean);
    const mostrarCartoes = itens.length === r.itens.length && itens.length > 0;
    const corpo = mostrarCartoes ? textos : linhas;
    balao.append(el("div", "", corpo[0] || ""));
    if (mostrarCartoes) {
      const grade = el("div", "produtos");
      itens.forEach((i) => grade.append(cartaoProduto(i, false)));
      balao.append(grade);
    }
    corpo.slice(1).forEach((t) => balao.append(el("div", "nota", t)));
  }
  linhaMensagem("cheek").append(balao);
  rolar();
}

function mostrarDigitando() {
  const linha = linhaMensagem("cheek");
  linha.classList.add("digitando");
  const b = el("div", "balao");
  b.append(el("i"), el("i"), el("i"));
  linha.append(b);
  rolar();
  return linha;
}

const botaoChat = document.querySelector("#form-chat button");

async function perguntarAoCheek(pergunta) {
  pergunta = pergunta.trim();
  if (!pergunta || botaoChat.disabled) return;
  mensagemCliente(pergunta);
  botaoChat.disabled = true;
  const digitando = mostrarDigitando();
  try {
    const [r] = await Promise.all([enviar("/chat", { pergunta }), espera(500)]);
    digitando.remove();
    mensagemCheek(r);
  } catch {
    digitando.remove();
    mensagemCheek({ resposta: "Não consegui responder agora. Tente de novo em instantes.", recusou: true, itens: [] });
  } finally {
    botaoChat.disabled = false;
    document.getElementById("pergunta").focus();
  }
}

document.getElementById("form-chat").addEventListener("submit", (e) => {
  e.preventDefault();
  const campo = document.getElementById("pergunta");
  const pergunta = campo.value;
  campo.value = "";
  perguntarAoCheek(pergunta);
});

document.querySelectorAll("[data-pergunta]").forEach((chip) =>
  chip.addEventListener("click", () => perguntarAoCheek(chip.dataset.pergunta)));

mensagemCheek({
  resposta: "Olá! Eu sou o Cheek. 👋\nPergunte sobre os produtos de limpeza do catálogo: tamanho, preço ou para que serve.\n"
    + "Se eu não souber, digo que não sei em vez de inventar.",
  recusou: false,
  itens: [],
});

// Conferência
const ICONES_STATUS = { encontrado: "✅", ambiguo: "⚠️", nao_encontrado: "❌", erro: "❌" };

function mostrarAviso(status, texto) {
  const a = document.getElementById("aviso");
  a.className = "aviso " + status;
  a.replaceChildren(el("span", "", ICONES_STATUS[status]), el("span", "", texto));
  a.hidden = false;
}

function nivel(semelhanca) {
  if (semelhanca >= 90) return ["", "Muito parecido"];
  if (semelhanca >= 80) return ["media", "Parecido"];
  return ["baixa", "Pouco parecido"];
}

function confirmar(c) {
  document.getElementById("confirmado-codigo").textContent = c.codigo;
  document.getElementById("confirmado-nome").textContent = `${c.nome} · ${c.unidade} · ${preco(c.preco)}`;
  const caixaOk = document.getElementById("confirmado");
  caixaOk.hidden = false;
  caixaOk.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function conferirItem(texto) {
  texto = texto.trim();
  if (!texto) return;
  const campo = document.getElementById("item");
  campo.value = texto;
  const lista = document.getElementById("candidatos");
  const botao = document.querySelector("#form-conferencia button");
  document.getElementById("confirmado").hidden = true;
  lista.replaceChildren();
  botao.disabled = true;
  let r;
  try {
    r = await enviar("/conferir-item", { texto });
  } catch {
    mostrarAviso("erro", "Não consegui conferir agora. Tente de novo.");
    return;
  } finally {
    botao.disabled = false;
  }
  mostrarAviso(r.status, r.mensagem);
  r.candidatos.forEach((c, posicao) => {
    const melhor = posicao === 0 && r.status === "encontrado";
    const card = el("div", "candidato" + (melhor ? " melhor" : ""));
    card.style.animationDelay = posicao * 70 + "ms";
    const info = el("div", "candidato-info");
    info.append(el("div", "produto-nome", c.nome));
    const meta = el("div", "candidato-meta");
    meta.append(el("span", "codigo", c.codigo), el("span", "etiqueta", c.unidade), el("span", "preco", preco(c.preco)));
    if (c.medida_confere === false) meta.append(el("span", "etiqueta medida-divergente", "⚠️ Tamanho diferente do digitado"));
    const [classe, rotulo] = nivel(c.semelhanca);
    const sem = el("div", "semelhanca");
    const barra = el("div", "barra");
    const preenchido = el("i", classe);
    preenchido.style.width = "0%";
    barra.append(preenchido);
    sem.append(barra, el("span", "", `${rotulo} (${Math.round(c.semelhanca)}%)`));
    info.append(meta, sem);
    const escolher = el("button", melhor ? "botao-principal" : "botao-secundario", "É este");
    escolher.type = "button";
    escolher.addEventListener("click", () => {
      lista.querySelectorAll(".candidato").forEach((outro) => {
        outro.classList.toggle("escolhido", outro === card);
        outro.classList.toggle("descartado", outro !== card);
      });
      confirmar(c);
    });
    card.append(el("span", "produto-emoji", emoji(c.nome)), info, escolher);
    lista.append(card);
    requestAnimationFrame(() => requestAnimationFrame(() => { preenchido.style.width = c.semelhanca + "%"; }));
  });
}

document.getElementById("form-conferencia").addEventListener("submit", (e) => {
  e.preventDefault();
  conferirItem(document.getElementById("item").value);
});

document.querySelectorAll("[data-item]").forEach((chip) =>
  chip.addEventListener("click", () => conferirItem(chip.dataset.item)));

document.getElementById("copiar-codigo").addEventListener("click", async () => {
  const codigo = document.getElementById("confirmado-codigo").textContent;
  try {
    await navigator.clipboard.writeText(codigo);
    aviso(`Código ${codigo} copiado`);
  } catch {
    aviso("Não deu para copiar. Selecione o código e copie à mão.");
  }
});

document.getElementById("conferir-outro").addEventListener("click", () => {
  const campo = document.getElementById("item");
  campo.value = "";
  document.getElementById("candidatos").replaceChildren();
  document.getElementById("aviso").hidden = true;
  document.getElementById("confirmado").hidden = true;
  campo.focus();
});

// Catálogo
function semAcento(t) {
  return t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function desenharCatalogo() {
  const termo = semAcento(document.getElementById("filtro").value.trim());
  const grade = document.getElementById("grade");
  const lista = catalogo.filter((i) => semAcento(`${i.codigo} ${i.nome} ${i.descricao} ${i.unidade}`).includes(termo));
  grade.replaceChildren(...lista.map((i) => cartaoProduto(i, true)));
  if (!lista.length) grade.append(el("p", "vazio", "Nenhum produto com esse nome no catálogo."));
  document.getElementById("contagem").textContent = `${lista.length} de ${catalogo.length} produtos`;
}

document.getElementById("filtro").addEventListener("input", desenharCatalogo);

carregarCatalogo();
