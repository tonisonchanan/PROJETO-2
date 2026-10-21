import pytest

from app import db


def test_importa_catalogo_de_amostra(conn):
    assert len(db.listar_itens(conn)) == 30


def test_reimportar_substitui_o_catalogo(conn, tmp_path):
    arquivo = tmp_path / "novo.csv"
    arquivo.write_text("codigo,nome,descricao,unidade,preco\n"
                       "AM001,Detergente Neutro 500 ml,Nova descrição,frasco 500 ml,\"3,50\"\n", encoding="utf-8")
    assert db.importar_csv(conn, arquivo) == 1
    itens = db.listar_itens(conn)
    assert len(itens) == 1
    assert itens[0]["preco"] == 3.5
    # O item antigo também sai da busca do chat.
    assert conn.execute("SELECT count(*) FROM itens_fts WHERE itens_fts MATCH 'amaciante'").fetchone()[0] == 0


def test_importacao_com_erro_mantem_o_catalogo(conn, tmp_path):
    arquivo = tmp_path / "ruim.csv"
    arquivo.write_text("codigo,nome,descricao,unidade,preco\nX1,Produto,Desc,un,abc\n", encoding="utf-8")
    with pytest.raises(db.ErroImportacao):
        db.importar_csv(conn, arquivo)
    assert len(db.listar_itens(conn)) == 30


def test_recusa_csv_vazio_para_nao_apagar_o_catalogo(conn, tmp_path):
    arquivo = tmp_path / "vazio.csv"
    arquivo.write_text("codigo,nome,descricao,unidade,preco\n", encoding="utf-8")
    with pytest.raises(db.ErroImportacao, match="nenhum item"):
        db.importar_csv(conn, arquivo)
    assert len(db.listar_itens(conn)) == 30


def test_recusa_csv_sem_colunas(conn, tmp_path):
    arquivo = tmp_path / "ruim.csv"
    arquivo.write_text("codigo,nome\nX1,Produto\n", encoding="utf-8")
    with pytest.raises(db.ErroImportacao, match="descricao, unidade, preco"):
        db.importar_csv(conn, arquivo)


def test_recusa_preco_invalido(conn, tmp_path):
    arquivo = tmp_path / "ruim.csv"
    arquivo.write_text("codigo,nome,descricao,unidade,preco\nX1,Produto,Desc,un,abc\n", encoding="utf-8")
    with pytest.raises(db.ErroImportacao, match="linha 2"):
        db.importar_csv(conn, arquivo)
