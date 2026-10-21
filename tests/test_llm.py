import urllib.error

import pytest

from app import llm
from app.chat import RECUSA, responder


@pytest.fixture
def ollama(monkeypatch):
    """Substitui a chamada ao Ollama por uma resposta fixa, para testar sem o modelo instalado."""
    def configurar(resposta=None, erro=None):
        def falso(pergunta, itens):
            if erro:
                raise erro
            return resposta
        monkeypatch.setattr(llm, "_chamar_ollama", falso)
    return configurar


def test_usa_texto_do_modelo_quando_confere(conn, ollama):
    ollama("Temos o Cloro Granulado para Piscina (AM026), pote de 1 kg, por R$ 29,00.")
    r = responder(conn, "tem cloro para piscina?", llm.gerador_ollama)
    assert r["resposta"].startswith("Temos o Cloro Granulado")


def test_preco_inventado_volta_para_o_modelo_de_texto(conn, ollama):
    ollama("Temos o Cloro Granulado para Piscina (AM026) por R$ 19,90.")
    r = responder(conn, "tem cloro para piscina?", llm.gerador_ollama)
    assert r["resposta"].startswith("Encontrei no catálogo:")
    assert "R$ 29,00" in r["resposta"]


def test_codigo_fora_dos_recuperados_volta_para_o_modelo_de_texto(conn, ollama):
    ollama("Temos o AM026 e também o AM099, que é ótimo para piscinas.")
    r = responder(conn, "tem cloro para piscina?", llm.gerador_ollama)
    assert r["resposta"].startswith("Encontrei no catálogo:")


def test_resposta_sem_citar_item_volta_para_o_modelo_de_texto(conn, ollama):
    ollama("Sim, temos cloro.")
    r = responder(conn, "tem cloro para piscina?", llm.gerador_ollama)
    assert r["resposta"].startswith("Encontrei no catálogo:")


def test_ollama_desligado_volta_para_o_modelo_de_texto(conn, ollama):
    ollama(erro=urllib.error.URLError("conexão recusada"))
    r = responder(conn, "tem cloro para piscina?", llm.gerador_ollama)
    assert r["recusou"] is False
    assert r["resposta"].startswith("Encontrei no catálogo:")


def test_fora_do_catalogo_nem_chama_o_modelo(conn, ollama):
    ollama(erro=AssertionError("o modelo não pode ser chamado"))
    assert responder(conn, "vocês vendem cimento?", llm.gerador_ollama)["resposta"] == RECUSA


def test_lista_enviada_ao_modelo_tem_so_os_itens_recuperados(itens):
    texto = llm._lista([i for i in itens if i["codigo"] == "AM026"])
    assert "AM026" in texto and "R$ 29,00" in texto
    assert "AM001" not in texto
