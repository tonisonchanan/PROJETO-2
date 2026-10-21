import os
import tempfile
from pathlib import Path

import pytest

# O servidor abre o banco ao ser importado, então o banco de teste é definido antes.
_tmp = tempfile.mkdtemp()
os.environ["CHEEK_DB"] = str(Path(_tmp) / "teste.db")

from app import db  # noqa: E402

CSV_AMOSTRA = Path(__file__).resolve().parent.parent / "dados" / "catalogo_amostra.csv"


@pytest.fixture
def conn():
    c = db.conectar(":memory:")
    db.importar_csv(c, CSV_AMOSTRA)
    return c


@pytest.fixture
def itens(conn):
    return db.listar_itens(conn)


@pytest.fixture
def cliente():
    from fastapi.testclient import TestClient

    from app import main
    db.importar_csv(main.conn, CSV_AMOSTRA)
    return TestClient(main.app)
