"""Conferência de item de pedido (RF004).

Não usa modelo de linguagem: a mesma entrada sempre devolve o mesmo resultado,
o que permite testar e explicar cada sugestão.
"""
from rapidfuzz import fuzz

from app.texto import chave_nome, medidas, normalizar

LIMIAR_MINIMO = 70     # abaixo disso o item não é sugerido
LIMIAR_CONFIANTE = 90  # a partir disso o item é considerado um bom candidato
MARGEM_AMBIGUIDADE = 5  # candidatos a menos de 5 pontos do primeiro são "empate"
PENALIDADE_MEDIDA = 25  # volume ou peso diferente do digitado
MAX_CANDIDATOS = 3


def _pontuar(consulta: str, item: dict) -> tuple[float, bool | None]:
    # O nome é comparado sem a medida; a medida entra depois, como penalidade.
    # Assim "Limpa Pedras 5 L" não fica parecido com "desinfetante 5 L" só por causa do "5 L".
    nota = fuzz.token_set_ratio(chave_nome(consulta), chave_nome(item["nome"]))
    medidas_consulta = medidas(consulta)
    if not medidas_consulta:
        return nota, None
    confere = bool(medidas_consulta & medidas(item["nome"]))
    if not confere:
        nota = max(0.0, nota - PENALIDADE_MEDIDA)
    return nota, confere


def conferir(texto: str, itens: list[dict]) -> dict:
    consulta = normalizar(texto)
    if not consulta:
        return {"status": "nao_encontrado", "mensagem": "Digite o nome ou o código do item.", "candidatos": []}

    por_codigo = [i for i in itens if i["codigo"].lower() == texto.strip().lower()]
    if por_codigo:
        return {"status": "encontrado", "mensagem": "Código encontrado no catálogo.",
                "candidatos": [{**por_codigo[0], "semelhanca": 100.0, "medida_confere": None}]}

    pontuados = []
    for item in itens:
        nota, confere = _pontuar(consulta, item)
        if nota >= LIMIAR_MINIMO:
            pontuados.append({**item, "semelhanca": round(nota, 1), "medida_confere": confere})
    # Desempate pelo código para que a ordem seja sempre a mesma.
    pontuados.sort(key=lambda c: (-c["semelhanca"], c["codigo"]))
    candidatos = pontuados[:MAX_CANDIDATOS]

    if not candidatos:
        return {"status": "nao_encontrado",
                "mensagem": "Nenhum item parecido no catálogo. Revise o nome digitado.",
                "candidatos": []}

    primeiro = candidatos[0]["semelhanca"]
    empatados = [c for c in candidatos[1:] if primeiro - c["semelhanca"] < MARGEM_AMBIGUIDADE]
    if primeiro >= LIMIAR_CONFIANTE and not empatados:
        status, mensagem = "encontrado", "Confirme se este é o item do pedido."
    elif all(c["medida_confere"] is False for c in candidatos):
        status = "ambiguo"
        mensagem = "O volume ou peso digitado não existe para este produto. Confirme com o cliente."
    else:
        status, mensagem = "ambiguo", "Há mais de um item possível. Confirme com o cliente qual é o correto."
    return {"status": status, "mensagem": mensagem, "candidatos": candidatos}
