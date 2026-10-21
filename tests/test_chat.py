import pytest

from app.chat import AVISO_SEGURANCA, RECUSA, responder


@pytest.mark.parametrize("pergunta", [
    "Vocês vendem cimento?",
    "Qual o prazo de entrega?",
    "Vocês entregam em Tubarão?",
    "tem tinta para parede?",
    "qual o horário de funcionamento?",
    "qual é o CNPJ da empresa?",
    "vocês aceitam pix?",
])
def test_recusa_o_que_nao_esta_no_catalogo(conn, pergunta):
    r = responder(conn, pergunta)
    assert r["recusou"] is True
    assert r["resposta"] == RECUSA


def test_recusa_sem_chamar_o_gerador(conn):
    def gerador_que_nao_pode_ser_chamado(pergunta, itens):
        raise AssertionError("o gerador foi chamado sem item recuperado")
    assert responder(conn, "vocês vendem cimento?", gerador_que_nao_pode_ser_chamado)["recusou"]


@pytest.mark.parametrize("pergunta, codigo", [
    ("Qual o preço do detergente neutro de 5 litros?", "AM002"),
    ("tem detergemte de limão?", "AM003"),
    ("O que vocês têm para limpar vidro?", "AM014"),
    ("tem cloro para piscina?", "AM026"),
    ("me indica um produto para tirar gordura do fogão", "AM017"),
])
def test_responde_com_item_do_catalogo(conn, pergunta, codigo):
    r = responder(conn, pergunta)
    assert r["recusou"] is False
    assert r["itens"][0] == codigo
    assert codigo in r["resposta"]


def test_gerador_so_recebe_itens_recuperados(conn):
    recebidos = []
    def gerador(pergunta, itens):
        recebidos.extend(i["codigo"] for i in itens)
        return "ok"
    responder(conn, "tem cloro para piscina?", gerador)
    assert recebidos == ["AM026"]


def test_informa_o_que_nao_encontrou(conn):
    r = responder(conn, "detergente para carro")
    assert r["recusou"] is False
    assert "carro" in r["resposta"]


@pytest.mark.parametrize("pergunta", [
    "posso misturar água sanitária com desinfetante?",
    "meu filho engoliu detergente, o que faço?",
    "caiu desengordurante no olho",
])
def test_pergunta_de_seguranca_nao_e_respondida(conn, pergunta):
    r = responder(conn, pergunta)
    assert r["recusou"] is True
    assert r["resposta"] == AVISO_SEGURANCA
