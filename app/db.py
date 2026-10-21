"""Banco do catálogo e do histórico (SQLite)."""
import csv
import os
import sqlite3
from pathlib import Path

COLUNAS = ["codigo", "nome", "descricao", "unidade", "preco"]
CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "cheek.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS itens (
    codigo    TEXT PRIMARY KEY,
    nome      TEXT NOT NULL,
    descricao TEXT NOT NULL,
    unidade   TEXT NOT NULL,
    preco     REAL NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS itens_fts USING fts5(
    codigo UNINDEXED, nome, descricao, unidade,
    tokenize = 'unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS historico (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    tipo      TEXT NOT NULL CHECK (tipo IN ('chat', 'conferencia')),
    entrada   TEXT NOT NULL,
    saida     TEXT NOT NULL,
    itens     TEXT NOT NULL DEFAULT ''
);
"""


class ErroImportacao(ValueError):
    pass


def conectar(caminho: str | Path | None = None) -> sqlite3.Connection:
    caminho = caminho or os.environ.get("CHEEK_DB", CAMINHO_PADRAO)
    conn = sqlite3.connect(caminho, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def importar_csv(conn: sqlite3.Connection, caminho: str | Path) -> int:
    """Substitui o catálogo pelos itens do CSV (RF001). Devolve o total importado.

    Item que não está no arquivo sai do catálogo: sobra de um catálogo antigo poderia
    aparecer na busca e ser confundido com um produto real.
    """
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        faltando = [c for c in COLUNAS if c not in (leitor.fieldnames or [])]
        if faltando:
            raise ErroImportacao(f"Colunas faltando no arquivo: {', '.join(faltando)}")
        linhas = []
        for n, linha in enumerate(leitor, start=2):
            try:
                preco = float(linha["preco"].replace(",", "."))
            except ValueError:
                raise ErroImportacao(f"Preço inválido na linha {n}: {linha['preco']!r}")
            if not linha["codigo"].strip() or not linha["nome"].strip():
                raise ErroImportacao(f"Código ou nome vazio na linha {n}")
            linhas.append((linha["codigo"].strip(), linha["nome"].strip(),
                           linha["descricao"].strip(), linha["unidade"].strip(), preco))
        if not linhas:
            raise ErroImportacao("O arquivo não tem nenhum item.")

    with conn:
        conn.execute("DELETE FROM itens")
        conn.executemany(
            "INSERT INTO itens VALUES (?, ?, ?, ?, ?) ON CONFLICT(codigo) DO UPDATE SET "
            "nome=excluded.nome, descricao=excluded.descricao, "
            "unidade=excluded.unidade, preco=excluded.preco",
            linhas,
        )
        conn.execute("DELETE FROM itens_fts")
        conn.execute("INSERT INTO itens_fts SELECT codigo, nome, descricao, unidade FROM itens")
    return len(linhas)


def listar_itens(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM itens ORDER BY codigo")]


def registrar(conn: sqlite3.Connection, tipo: str, entrada: str, saida: str, itens: list[str]) -> None:
    """Grava no histórico (RF005). Uma falha aqui não pode derrubar a resposta ao usuário."""
    try:
        with conn:
            conn.execute(
                "INSERT INTO historico (tipo, entrada, saida, itens) VALUES (?, ?, ?, ?)",
                (tipo, entrada, saida, ",".join(itens)),
            )
    except sqlite3.Error:
        pass
