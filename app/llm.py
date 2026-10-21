"""Redação da resposta do chat por um modelo de linguagem local (Ollama).

O modelo só recebe os itens que a busca já recuperou e só redige o texto.
Se o Ollama não estiver rodando, demorar demais ou citar um código que não foi
recuperado, a resposta volta para o modelo de texto de chat.gerador_por_modelo.
Não há chave de API: o Ollama roda no próprio computador.
"""
import json
import os
import re
import urllib.error
import urllib.request

from app.chat import formatar_preco, gerador_por_modelo

URL = os.environ.get("CHEEK_OLLAMA_URL", "http://localhost:11434")
MODELO = os.environ.get("CHEEK_OLLAMA_MODELO", "qwen2.5:0.5b")
TEMPO_LIMITE = float(os.environ.get("CHEEK_OLLAMA_TEMPO", "10"))

INSTRUCAO = (
    "Você é o Cheek, atendente virtual de uma fabricante de produtos de limpeza. "
    "Responda em português do Brasil, em no máximo quatro frases, usando SOMENTE os itens "
    "da lista abaixo. Cite o código de cada item mencionado. Não invente preço, prazo, estoque, "
    "frete, modo de uso nem orientação de segurança. Se a lista não responder à pergunta, diga "
    "que a informação não consta no catálogo e oriente falar com a equipe de atendimento."
)

_CODIGO = re.compile(r"\b[A-Z]+\d{2,}\b")
_PRECO = re.compile(r"R\$\s*(\d+(?:[.,]\d{1,2})?)")


def _lista(itens: list[dict]) -> str:
    return "\n".join(
        f"- código {i['codigo']}: {i['nome']}; {i['descricao']}; unidade {i['unidade']}; "
        f"preço {formatar_preco(i['preco'])}"
        for i in itens
    )


def _chamar_ollama(pergunta: str, itens: list[dict]) -> str:
    corpo = {
        "model": MODELO,
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": f"{INSTRUCAO}\n\nItens do catálogo:\n{_lista(itens)}"},
            {"role": "user", "content": pergunta},
        ],
    }
    pedido = urllib.request.Request(
        f"{URL}/api/chat", data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE) as resposta:
        return json.load(resposta)["message"]["content"].strip()


def resposta_confere(texto: str, itens: list[dict]) -> bool:
    """A resposta só vale se citar algum item recuperado, nenhum código de fora e nenhum preço inventado."""
    codigos = {i["codigo"] for i in itens}
    if not any(c in texto for c in codigos):
        return False
    if set(_CODIGO.findall(texto)) - codigos:
        return False
    precos = {round(i["preco"], 2) for i in itens}
    return all(round(float(p.replace(",", ".")), 2) in precos for p in _PRECO.findall(texto))


def gerador_ollama(pergunta: str, itens: list[dict]) -> str:
    try:
        texto = _chamar_ollama(pergunta, itens)
    except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError):
        return gerador_por_modelo(pergunta, itens)
    if not resposta_confere(texto, itens):
        return gerador_por_modelo(pergunta, itens)
    return texto
