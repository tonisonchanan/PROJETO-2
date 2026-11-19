"""Resposta do chat (RF002 e RF003).

A geração da resposta fica numa função separada para que um modelo de linguagem
possa ser plugado depois, sem mudar a regra principal: sem item recuperado,
não há resposta, e o modelo nunca é chamado.
"""
import sqlite3
from typing import Callable

from app.busca import Resultado, buscar
from app.texto import normalizar

RECUSA = ("Não encontrei essa informação no catálogo. "
          "Para isso, fale com a equipe de atendimento.")

# Perguntas de segurança no uso de produto químico nunca são respondidas pelo Cheek,
# mesmo que o produto esteja no catálogo: a orientação certa está no rótulo e na FISPQ.
TERMOS_SEGURANCA = ("misturar", "mistura", "misturo", "engoli", "ingeri", "ingerir", "beber", "bebeu",
                    "intoxica", "olho", "olhos", "pele", "queimadura", "respirar", "inalar", "inalei",
                    "crianca", "gravida", "gestante", "animal", "cachorro", "gato")
AVISO_SEGURANCA = ("Por segurança, não oriento sobre mistura de produtos, contato com pele ou olhos, "
                   "ingestão ou inalação. Siga o rótulo e a ficha de segurança (FISPQ) do produto e "
                   "fale com a equipe de atendimento. Em caso de acidente, procure atendimento médico ou ligue 192 (SAMU).")

Gerador = Callable[[str, list[dict]], str]


def formatar_preco(valor: float) -> str:
    return f"R$ {valor:.2f}".replace(".", ",")


def gerador_por_modelo(pergunta: str, itens: list[dict]) -> str:
    """Resposta montada só com os dados dos itens recuperados, sem modelo de linguagem."""
    linhas = ["Encontrei no catálogo:"]
    for i in itens:
        linhas.append(f"- {i['nome']} (código {i['codigo']}): {i['descricao']}. "
                      f"Unidade: {i['unidade']}. Preço: {formatar_preco(i['preco'])}.")
    return "\n".join(linhas)


def responder(conn: sqlite3.Connection, pergunta: str, gerador: Gerador = gerador_por_modelo) -> dict:
    palavras = normalizar(pergunta).split()
    if any(p.startswith(t) for p in palavras for t in TERMOS_SEGURANCA):
        return {"resposta": AVISO_SEGURANCA, "recusou": True, "itens": []}

    resultado: Resultado = buscar(conn, pergunta)
    if not resultado.itens:
        return {"resposta": RECUSA, "recusou": True, "itens": []}

    resposta = gerador(pergunta, resultado.itens)
    if resultado.mais_resultados:
        resposta += "\nHá outros itens parecidos. Informe o nome do produto para eu refinar a busca."
    if resultado.nao_encontradas:
        resposta += ("\nNão encontrei no catálogo nada sobre: "
                     f"{', '.join(resultado.nao_encontradas)}. Para isso, fale com a equipe de atendimento.")
    return {"resposta": resposta, "recusou": False, "itens": [i["codigo"] for i in resultado.itens]}
