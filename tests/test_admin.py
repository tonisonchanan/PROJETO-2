"""Área administrativa: login (RF006), importação pela tela (RF001) e histórico (RF005)."""
from tests.conftest import CSV_AMOSTRA

CSV_NOVO = ("codigo,nome,descricao,unidade,preco\n"
            "N1,Detergente Teste 500 ml,Descrição,frasco 500 ml,\"2,99\"\n"
            "N2,Cloro Teste 5 L,Descrição,5 L,15.00\n")


def entrar(cliente, senha="senha-de-teste"):
    return cliente.post("/admin/entrar", json={"usuario": "admin", "senha": senha})


def test_login_errado_nao_diz_qual_campo_errou(cliente):
    r1 = entrar(cliente, senha="errada")
    r2 = cliente.post("/admin/entrar", json={"usuario": "outro", "senha": "senha-de-teste"})
    assert r1.status_code == r2.status_code == 401
    assert r1.json()["detail"] == r2.json()["detail"] == "Usuário ou senha incorretos."
    assert cliente.get("/admin/sessao").json()["autenticado"] is False


def test_rotas_administrativas_exigem_login(cliente):
    cliente.cookies.clear()
    assert cliente.get("/admin/historico").status_code == 401
    assert cliente.post("/admin/importar", json={"conteudo": CSV_NOVO}).status_code == 401


def test_login_libera_e_sair_bloqueia(cliente):
    assert entrar(cliente).status_code == 200
    assert cliente.get("/admin/sessao").json()["autenticado"] is True
    assert cliente.get("/admin/historico").status_code == 200
    cliente.post("/admin/sair")
    assert cliente.get("/admin/historico").status_code == 401


def test_importar_pela_tela_substitui_o_catalogo(cliente):
    entrar(cliente)
    r = cliente.post("/admin/importar", json={"conteudo": CSV_NOVO})
    assert r.status_code == 200 and r.json() == {"importados": 2}
    codigos = [i["codigo"] for i in cliente.get("/itens").json()]
    assert codigos == ["N1", "N2"]
    # O chat passa a enxergar só o catálogo novo.
    assert cliente.post("/chat", json={"pergunta": "tem amaciante?"}).json()["recusou"] is True
    assert cliente.post("/chat", json={"pergunta": "tem detergente?"}).json()["itens"] == ["N1"]


def test_importacao_com_erro_mantem_catalogo_e_explica(cliente):
    entrar(cliente)
    antes = cliente.get("/itens").json()
    r = cliente.post("/admin/importar", json={"conteudo": "codigo,nome\nX,Y\n"})
    assert r.status_code == 400
    assert "descricao, unidade, preco" in r.json()["detail"]
    assert cliente.get("/itens").json() == antes


def test_importa_o_csv_de_amostra_pela_tela(cliente):
    entrar(cliente)
    conteudo = CSV_AMOSTRA.read_text(encoding="utf-8-sig")
    assert cliente.post("/admin/importar", json={"conteudo": conteudo}).json() == {"importados": 30}


def test_historico_mostra_o_mais_recente_primeiro_e_filtra(cliente):
    entrar(cliente)
    cliente.post("/chat", json={"pergunta": "vocês vendem cimento?"})
    cliente.post("/conferir-item", json={"texto": "agua sanitaria 5 L"})
    todos = cliente.get("/admin/historico").json()
    assert todos[0]["tipo"] == "conferencia" and todos[0]["itens"].startswith("AM009")
    assert todos[1]["entrada"] == "vocês vendem cimento?"
    so_chat = cliente.get("/admin/historico", params={"tipo": "chat"}).json()
    assert so_chat and all(h["tipo"] == "chat" for h in so_chat)
    assert cliente.get("/admin/historico", params={"tipo": "outro"}).status_code == 400


def test_historico_nao_tem_campo_de_dado_pessoal(cliente):
    entrar(cliente)
    cliente.post("/chat", json={"pergunta": "tem detergente?"})
    registro = cliente.get("/admin/historico").json()[0]
    assert set(registro) == {"id", "criado_em", "tipo", "entrada", "saida", "itens"}
