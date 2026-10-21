async function enviar(rota, corpo) {
  const resposta = await fetch(rota, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  if (!resposta.ok) throw new Error("Erro " + resposta.status);
  return resposta.json();
}

document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".aba, .painel").forEach((el) => el.classList.remove("ativa", "ativo"));
    botao.classList.add("ativa");
    document.getElementById(botao.dataset.aba).classList.add("ativo");
  });
});

function adicionarMensagem(texto, classes) {
  const div = document.createElement("div");
  div.className = "msg " + classes;
  div.textContent = texto;
  const caixa = document.getElementById("mensagens");
  caixa.appendChild(div);
  caixa.scrollTop = caixa.scrollHeight;
}

document.getElementById("form-chat").addEventListener("submit", async (e) => {
  e.preventDefault();
  const campo = document.getElementById("pergunta");
  const pergunta = campo.value.trim();
  if (!pergunta) return;
  adicionarMensagem(pergunta, "cliente");
  campo.value = "";
  try {
    const r = await enviar("/chat", { pergunta });
    adicionarMensagem(r.resposta, r.recusou ? "cheek recusa" : "cheek");
  } catch {
    adicionarMensagem("Não consegui responder agora. Tente de novo.", "cheek recusa");
  }
});

document.getElementById("form-conferencia").addEventListener("submit", async (e) => {
  e.preventDefault();
  const texto = document.getElementById("item").value.trim();
  const tabela = document.getElementById("candidatos");
  const corpo = tabela.querySelector("tbody");
  document.getElementById("confirmado").textContent = "";
  corpo.innerHTML = "";
  let r;
  try {
    r = await enviar("/conferir-item", { texto });
  } catch {
    document.getElementById("aviso").textContent = "Não consegui conferir agora. Tente de novo.";
    tabela.hidden = true;
    return;
  }
  document.getElementById("aviso").textContent = r.mensagem;
  tabela.hidden = r.candidatos.length === 0;
  r.candidatos.forEach((c) => {
    const linha = document.createElement("tr");
    [c.codigo, c.nome, c.unidade, c.semelhanca + "%"].forEach((valor) => {
      const td = document.createElement("td");
      td.textContent = valor;
      linha.appendChild(td);
    });
    if (c.medida_confere === false) {
      linha.children[2].classList.add("divergente");
      linha.children[2].textContent += " (volume diferente do digitado)";
    }
    const celula = document.createElement("td");
    const botao = document.createElement("button");
    botao.className = "escolher";
    botao.textContent = "É este";
    botao.addEventListener("click", () => {
      document.getElementById("confirmado").textContent = `Código para o pedido: ${c.codigo} · ${c.nome}`;
    });
    celula.appendChild(botao);
    linha.appendChild(celula);
    corpo.appendChild(linha);
  });
});
