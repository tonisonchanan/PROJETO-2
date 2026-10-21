def test_rota_conferir_item(cliente):
    r = cliente.post("/conferir-item", json={"texto": "agua sanitaria 5 L"})
    assert r.status_code == 200
    assert r.json()["candidatos"][0]["codigo"] == "AM009"


def test_rota_chat_recusa(cliente):
    r = cliente.post("/chat", json={"pergunta": "vocês vendem cimento?"})
    assert r.status_code == 200
    assert r.json()["recusou"] is True


def test_entrada_vazia_e_rejeitada(cliente):
    assert cliente.post("/chat", json={"pergunta": ""}).status_code == 422
    assert cliente.post("/conferir-item", json={}).status_code == 422


def test_historico_e_gravado(cliente):
    from app import main
    antes = main.conn.execute("SELECT count(*) FROM historico").fetchone()[0]
    cliente.post("/chat", json={"pergunta": "tem amaciante?"})
    depois = main.conn.execute("SELECT count(*) FROM historico").fetchone()[0]
    assert depois == antes + 1


def test_pagina_inicial(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "Cheek" in r.text
