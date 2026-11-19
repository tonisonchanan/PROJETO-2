"""O conjunto de perguntas de teste roda a cada versão (atributo Verificabilidade)."""
from experimentos.rodar import main


def test_conjunto_de_perguntas_de_teste_confere():
    assert main() == 0
