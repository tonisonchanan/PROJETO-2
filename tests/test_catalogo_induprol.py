"""Confere o catálogo real da Induprol, além da amostra fictícia usada nos outros testes."""
from pathlib import Path

import pytest

from app import db
from app.chat import responder
from app.conferencia import conferir

CSV_INDUPROL = Path(__file__).resolve().parent.parent / "dados" / "catalogo_induprol.csv"


@pytest.fixture(scope="module")
def conn_induprol():
    c = db.conectar(":memory:")
    db.importar_csv(c, CSV_INDUPROL)
    return c


def test_importa_os_96_itens_com_preco(conn_induprol):
    itens = db.listar_itens(conn_induprol)
    assert len(itens) == 96
    assert all(i["preco"] > 0 for i in itens)


@pytest.mark.parametrize("texto, certo", [
    ("cloro 5L", "HGHXKCFDD"),
    ("alvejante sem cloro", "WC85FKEGR"),
    ("desinfetante lavanda", "87FXBFSR8-LAV"),
    ("HGHXKCFDD", "HGHXKCFDD"),
])
def test_conferencia_no_catalogo_real(conn_induprol, texto, certo):
    r = conferir(texto, db.listar_itens(conn_induprol))
    assert r["status"] == "encontrado"
    assert r["candidatos"][0]["codigo"] == certo


def test_agua_sanitaria_sem_variacao_pede_confirmacao(conn_induprol):
    # A loja tem a comum e a perfumada, com preços diferentes.
    r = conferir("agua sanitaria", db.listar_itens(conn_induprol))
    assert r["status"] == "ambiguo"
    assert {c["codigo"] for c in r["candidatos"]} == {"X2TYNZVVG-COM", "X2TYNZVVG-PERF"}


def test_chat_no_catalogo_real(conn_induprol):
    assert "HGHXKCFDD" in responder(conn_induprol, "tem cloro?")["itens"]
    assert "WC85FKEGR" not in responder(conn_induprol, "tem cloro?")["itens"]
    assert responder(conn_induprol, "vocês vendem cimento?")["recusou"] is True
