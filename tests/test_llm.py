"""Modelo de linguagem opcional: só o que vem do catálogo passa (RF002)."""
from app import llm
from app.chat import gerador_por_modelo

ITENS = [
    {"codigo": "HGHXKCFDD", "nome": "Cloro 5L", "descricao": "Cloro", "unidade": "5 L", "preco": 23.5},
    {"codigo": "87FXBFSR8-LAV", "nome": "Desinfetante 5L - Lavanda", "descricao": "D", "unidade": "5 L", "preco": 18.0},
]


def test_resposta_fiel_ao_catalogo_passa():
    assert llm.resposta_confere("Temos o Cloro 5L (código HGHXKCFDD) por R$ 23,50.", ITENS)
    assert llm.resposta_confere("O Desinfetante Lavanda (87FXBFSR8-LAV) custa R$ 18,00.", ITENS)


def test_preco_inventado_e_descartado():
    assert not llm.resposta_confere("O Cloro 5L (HGHXKCFDD) sai por R$ 19,90.", ITENS)


def test_codigo_fora_dos_recuperados_e_descartado():
    assert not llm.resposta_confere("Temos HGHXKCFDD e também o X2TYNZVVG-COM.", ITENS)


def test_resposta_sem_codigo_e_descartada():
    assert not llm.resposta_confere("Temos cloro, sim!", ITENS)


def test_sem_chave_fica_desligado(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm.ativo() is False


def test_falha_da_api_volta_para_o_texto_montado(monkeypatch):
    def falha(*_):
        raise TimeoutError("demorou")
    monkeypatch.setattr(llm, "_chamar_modelo", falha)
    assert llm.gerador_llm("tem cloro?", ITENS) == gerador_por_modelo("tem cloro?", ITENS)


def test_resposta_inventada_volta_para_o_texto_montado(monkeypatch):
    monkeypatch.setattr(llm, "_chamar_modelo", lambda *_: "Cloro HGHXKCFDD por R$ 5,00, entrega amanhã.")
    assert llm.gerador_llm("tem cloro?", ITENS) == gerador_por_modelo("tem cloro?", ITENS)


def test_resposta_fiel_e_usada(monkeypatch):
    texto = "Temos o Cloro 5L, código HGHXKCFDD, por R$ 23,50."
    monkeypatch.setattr(llm, "_chamar_modelo", lambda *_: texto)
    assert llm.gerador_llm("tem cloro?", ITENS) == texto


def test_recusa_nao_chama_o_modelo(conn, monkeypatch):
    from app import chat
    chamadas = []
    monkeypatch.setattr(llm, "_chamar_modelo", lambda *a: chamadas.append(a) or "x")
    r = chat.responder(conn, "vocês vendem cimento?", gerador=llm.gerador_llm)
    assert r["recusou"] and chamadas == []
