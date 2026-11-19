"""Roda o conjunto de perguntas de teste contra o catálogo real e mostra o resultado.

Uso: python -m experimentos.rodar [--md]

Usa um banco em memória com dados/catalogo_induprol.csv, então não mexe no banco do servidor.
O resultado de cada linha é comparado com o esperado em experimentos/perguntas_teste.csv.
"""
import csv
import sys
from pathlib import Path

from app import chat, conferencia, db

RAIZ = Path(__file__).resolve().parent.parent
PERGUNTAS = RAIZ / "experimentos" / "perguntas_teste.csv"
CATALOGO = RAIZ / "dados" / "catalogo_induprol.csv"


def avaliar(conn, itens, linha: dict) -> tuple[str, list[str], bool]:
    esperado, codigo = linha["esperado"], linha["codigo_esperado"]
    if linha["rota"] == "chat":
        r = chat.responder(conn, linha["entrada"])
        codigos = r["itens"]
        if r["resposta"] == chat.AVISO_SEGURANCA:
            obtido = "seguranca"
        elif r["recusou"]:
            obtido = "recusa"
        elif "Não encontrei no catálogo nada sobre" in r["resposta"]:
            obtido = "parcial"
        else:
            obtido = "responde"
        ok = obtido == esperado and (not codigo or codigo in codigos)
    else:
        r = conferencia.conferir(linha["entrada"], itens)
        codigos = [c["codigo"] for c in r["candidatos"]]
        obtido = r["status"]
        ok = obtido == esperado and (not codigo or (codigos and codigos[0] == codigo))
    return obtido, codigos, ok


def main() -> int:
    conn = db.conectar(":memory:")
    db.importar_csv(conn, CATALOGO)
    itens = db.listar_itens(conn)
    linhas = list(csv.DictReader(open(PERGUNTAS, encoding="utf-8")))
    resultados = [(l, *avaliar(conn, itens, l)) for l in linhas]
    acertos = sum(ok for *_, ok in resultados)

    if "--md" in sys.argv:
        print("| ID | Entrada | Esperado | Obtido | Códigos devolvidos | Confere |")
        print("|---|---|---|---|---|---|")
        for l, obtido, codigos, ok in resultados:
            print(f"| {l['id']} | {l['entrada']} | {l['esperado']} {l['codigo_esperado']} | {obtido} | "
                  f"{', '.join(codigos[:3])} | {'sim' if ok else 'NÃO'} |")
    else:
        for l, obtido, codigos, ok in resultados:
            marca = "ok " if ok else "ERR"
            print(f"{marca} {l['id']} {l['entrada'][:45]:45} esperado={l['esperado']:<14} "
                  f"obtido={obtido:<14} {', '.join(codigos[:3])}")
    print(f"\n{acertos} de {len(resultados)} conferem com o esperado.")
    return 0 if acertos == len(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
