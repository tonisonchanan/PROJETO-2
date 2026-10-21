import pytest

from app.conferencia import conferir


def codigos(resultado):
    return [c["codigo"] for c in resultado["candidatos"]]


@pytest.mark.parametrize("texto, esperado", [
    ("desinfetante lavanda 5l", "AM005"),
    ("Desinfetante Lavanda 5 L", "AM005"),
    ("desinfetamte lavamda 5 litros", "AM005"),  # erro de digitação
    ("detergente neutro 5 L", "AM002"),
    ("agua sanitaria 5l", "AM009"),
    ("amaciante 2 litros", "AM011"),
    ("limpa piso", "AM019"),
    ("AM009", "AM009"),
    ("am009", "AM009"),
])
def test_encontra_o_item_certo(itens, texto, esperado):
    r = conferir(texto, itens)
    assert r["status"] == "encontrado"
    assert codigos(r)[0] == esperado


def test_volume_diferente_nao_fica_em_primeiro(itens):
    # O erro relatado pela Induprol: o item certo com volume errado.
    r = conferir("desinfetante lavanda 5 L", itens)
    lavanda_2l = next(c for c in r["candidatos"] if c["codigo"] == "AM004")
    assert lavanda_2l["medida_confere"] is False
    assert lavanda_2l["semelhanca"] < r["candidatos"][0]["semelhanca"]


@pytest.mark.parametrize("texto, possiveis", [
    ("desinfetante lavanda", {"AM004", "AM005"}),  # falta o volume
    ("detergente 500ml", {"AM001", "AM003"}),
])
def test_sem_informacao_suficiente_pede_confirmacao(itens, texto, possiveis):
    r = conferir(texto, itens)
    assert r["status"] == "ambiguo"
    assert possiveis <= set(codigos(r))


@pytest.mark.parametrize("texto, certo, errado", [
    ("cloro", "AM026", "AM010"),
    ("alvejante sem cloro", "AM010", "AM026"),
])
def test_sem_cloro_nao_empata_com_cloro(itens, texto, certo, errado):
    # token_set_ratio sozinho ignora o "sem" e dava empate em 100 entre os dois.
    r = conferir(texto, itens)
    assert codigos(r)[0] == certo
    notas = {c["codigo"]: c["semelhanca"] for c in r["candidatos"]}
    assert notas.get(errado, 0) < notas[certo] - 20


def test_palavra_a_mais_na_consulta_desempata(itens):
    # O item que tem todas as palavras digitadas fica na frente.
    r = conferir("detergente limao", itens)
    assert r["status"] == "encontrado"
    assert codigos(r)[0] == "AM003"


def test_volume_inexistente_avisa(itens):
    r = conferir("desinfetante eucalipto 1 L", itens)
    assert r["status"] == "ambiguo"
    assert "volume" in r["mensagem"]


@pytest.mark.parametrize("texto", ["cimento", "tinta", "parafuso 5mm", "   "])
def test_item_fora_do_catalogo(itens, texto):
    r = conferir(texto, itens)
    assert r["status"] == "nao_encontrado"
    assert r["candidatos"] == []


def test_resultado_e_deterministico(itens):
    primeiro = conferir("detergente", itens)
    for _ in range(20):
        assert conferir("detergente", itens) == primeiro
