"""Uso: python -m app.importar dados/catalogo_induprol.csv"""
import sys

from app.db import ErroImportacao, conectar, importar_csv

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    try:
        total = importar_csv(conectar(), sys.argv[1])
    except ErroImportacao as e:
        sys.exit(f"Importação recusada. {e}")
    print(f"{total} itens importados.")
