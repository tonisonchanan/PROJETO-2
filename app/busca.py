"""Recuperação de itens do catálogo para o chat (parte "R" do RAG).

Busca por texto no próprio SQLite (FTS5). Com cerca de 150 itens não há ganho
em usar banco vetorial, e a busca por palavra é fácil de explicar e de testar.
"""
import sqlite3
from dataclasses import dataclass, field

from rapidfuzz import fuzz, process

from app.conferencia import contradiz_negacao
from app.texto import chave_nome, medidas, normalizar, palavras_chave

MAX_ITENS = 5
CORTE_CORRECAO = 85  # semelhança mínima para corrigir um erro de digitação


@dataclass
class Resultado:
    itens: list[dict]
    nao_encontradas: list[str] = field(default_factory=list)
    mais_resultados: bool = False


def _vocabulario(conn: sqlite3.Connection) -> set[str]:
    palavras = set()
    for linha in conn.execute("SELECT nome, descricao, unidade FROM itens"):
        palavras.update(normalizar(" ".join(linha)).split())
    return palavras


def _variacoes(palavra: str) -> list[str]:
    """Singular e plural simples: "vidro" também acha "vidros", e vice-versa."""
    if palavra.endswith("s") and len(palavra) > 3:
        return [palavra, palavra[:-1]]
    return [palavra, palavra + "s"]


def _corrigir(palavra: str, vocabulario: set[str]) -> str | None:
    """Troca "detergemte" por "detergente". Devolve None se não houver palavra parecida."""
    if any(v in vocabulario for v in _variacoes(palavra)):
        return palavra
    if len(palavra) < 5:
        return None
    achado = process.extractOne(palavra, vocabulario, scorer=fuzz.ratio, score_cutoff=CORTE_CORRECAO)
    return achado[0] if achado else None


def buscar(conn: sqlite3.Connection, pergunta: str) -> Resultado:
    vocabulario = _vocabulario(conn)
    medidas_pedidas = medidas(pergunta)
    termos, nao_encontradas = [], []
    for palavra in palavras_chave(pergunta):
        if palavra in medidas_pedidas or palavra.replace(".", "").isdigit():
            continue
        corrigida = _corrigir(palavra, vocabulario)
        if corrigida:
            termos.append(corrigida)
        else:
            nao_encontradas.append(palavra)

    if not termos:
        return Resultado(itens=[], nao_encontradas=nao_encontradas)

    # Primeiro exige todas as palavras ("cloro piscina" só traz o cloro de piscina).
    # Se nada tiver todas, aceita qualquer uma delas.
    grupos = ["(" + " OR ".join(f'"{v}"' for v in _variacoes(t)) + ")" for t in dict.fromkeys(termos)]
    itens = []
    for operador in (" AND ", " OR "):
        linhas = conn.execute(
            "SELECT i.* FROM itens_fts f JOIN itens i ON i.codigo = f.codigo "
            "WHERE itens_fts MATCH ? ORDER BY bm25(itens_fts), i.codigo",
            (operador.join(grupos),),
        ).fetchall()
        itens = [dict(r) for r in linhas]
        if itens:
            break

    # "tem cloro?" não deve trazer o "Alvejante sem cloro", e vice-versa.
    pergunta_chave = chave_nome(pergunta)
    itens = [i for i in itens if not contradiz_negacao(pergunta_chave, chave_nome(i["nome"]))]

    # Se o cliente falou em "5 L", os itens com essa medida vêm primeiro.
    if medidas_pedidas:
        itens.sort(key=lambda i: not (medidas(i["nome"]) & medidas_pedidas))
    return Resultado(itens=itens[:MAX_ITENS], nao_encontradas=nao_encontradas,
                     mais_resultados=len(itens) > MAX_ITENS)
