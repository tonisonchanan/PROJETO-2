"""Redação da resposta do chat por modelo de linguagem (Claude API), opcional.

Só entra em uso quando a variável de ambiente ANTHROPIC_API_KEY está definida.
A chave nunca fica no código. Sem chave, o chat continua com o texto montado
direto do catálogo (chat.gerador_por_modelo).

O modelo recebe apenas os itens que a busca já recuperou e só redige o texto.
A resposta é descartada, e vale o texto montado, quando (RF002):
- a API não responde em CHEEK_LLM_TEMPO segundos (padrão 10) ou dá erro;
- o modelo recusa;
- o texto não cita nenhum código recuperado, cita um código que não foi recuperado
  ou traz um preço que não é de nenhum item recuperado.
"""
import os
import re

from app.chat import formatar_preco, gerador_por_modelo

MODELO = os.environ.get("CHEEK_LLM_MODELO", "claude-opus-5-5")
TEMPO_LIMITE = float(os.environ.get("CHEEK_LLM_TEMPO", "10"))

INSTRUCAO = (
    "Você é o Cheek, atendente virtual da Induprol, fabricante de produtos de limpeza. "
    "Responda em português do Brasil, em no máximo quatro frases curtas, usando SOMENTE os itens "
    "da lista enviada. Cite o código de cada item que mencionar, exatamente como está na lista. "
    "Use os preços exatamente como estão na lista. Não invente preço, prazo, estoque, frete, forma "
    "de pagamento, modo de uso nem orientação de segurança. Se a lista não responder à pergunta, "
    "diga que a informação não consta no catálogo e oriente falar com a equipe de atendimento."
)

# Parece código de produto: maiúsculas e números, com ao menos um número ou nove caracteres.
_TOKEN_CODIGO = re.compile(r"\b[A-Z0-9]{5,}(?:-[A-Z0-9]+)*\b")
_PRECO = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)")

_cliente = None


def ativo() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _parece_codigo(token: str) -> bool:
    base = token.split("-")[0]
    return any(ch.isdigit() for ch in base) or len(base) >= 9


def _valor(texto_preco: str) -> float:
    if "," in texto_preco:
        texto_preco = texto_preco.replace(".", "").replace(",", ".")
    return round(float(texto_preco), 2)


def resposta_confere(texto: str, itens: list[dict]) -> bool:
    codigos = {i["codigo"] for i in itens}
    if not any(c in texto for c in codigos):
        return False
    citados = {t for t in _TOKEN_CODIGO.findall(texto) if _parece_codigo(t)}
    if any(not any(t == c or t in c for c in codigos) for t in citados):
        return False
    precos = {round(i["preco"], 2) for i in itens}
    return all(_valor(p) in precos for p in _PRECO.findall(texto))


def _lista(itens: list[dict]) -> str:
    return "\n".join(
        f"- código {i['codigo']}: {i['nome']}; {i['descricao']}; unidade {i['unidade'] or 'não informada'}; "
        f"preço {formatar_preco(i['preco'])}"
        for i in itens
    )


def _chamar_modelo(pergunta: str, itens: list[dict]) -> str | None:
    global _cliente
    import anthropic  # só é necessário quando a chave existe

    if _cliente is None:
        _cliente = anthropic.Anthropic(timeout=TEMPO_LIMITE, max_retries=0)
    resposta = _cliente.beta.messages.create(
        model=MODELO,
        max_tokens=2048,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=INSTRUCAO,
        messages=[{"role": "user", "content": f"Itens do catálogo:\n{_lista(itens)}\n\nPergunta do cliente: {pergunta}"}],
    )
    if resposta.stop_reason != "end_turn":
        return None
    texto = "".join(b.text for b in resposta.content if b.type == "text").strip()
    return texto or None


def gerador_llm(pergunta: str, itens: list[dict]) -> str:
    try:
        texto = _chamar_modelo(pergunta, itens)
    except Exception:  # qualquer falha da API cai no texto montado; o atendimento não para
        return gerador_por_modelo(pergunta, itens)
    if not texto or not resposta_confere(texto, itens):
        return gerador_por_modelo(pergunta, itens)
    return texto
