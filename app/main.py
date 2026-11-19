"""Servidor do Cheek. Rodar com: uvicorn app.main:app --reload"""
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import admin, chat, conferencia, db, llm

PASTA_STATIC = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Cheek", description="Assistente de atendimento restrito ao catálogo")
conn = db.conectar()

if (_aviso := admin.aviso_de_inicio()):
    print(_aviso, flush=True)
print(f"Chat: redigido pelo modelo {llm.MODELO}." if llm.ativo()
      else "Chat: sem ANTHROPIC_API_KEY, respostas montadas direto do catálogo.", flush=True)


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1, max_length=500)


class ItemDigitado(BaseModel):
    texto: str = Field(min_length=1, max_length=200)


@app.post("/chat")
def rota_chat(entrada: Pergunta) -> dict:
    gerador = llm.gerador_llm if llm.ativo() else chat.gerador_por_modelo
    resultado = chat.responder(conn, entrada.pergunta, gerador=gerador)
    db.registrar(conn, "chat", entrada.pergunta, resultado["resposta"], resultado["itens"])
    return resultado


@app.post("/conferir-item")
def rota_conferir(entrada: ItemDigitado) -> dict:
    resultado = conferencia.conferir(entrada.texto, db.listar_itens(conn))
    db.registrar(conn, "conferencia", entrada.texto, resultado["status"],
                 [c["codigo"] for c in resultado["candidatos"]])
    return resultado


@app.get("/itens")
def rota_itens() -> list[dict]:
    return db.listar_itens(conn)


class Login(BaseModel):
    usuario: str = Field(max_length=100)
    senha: str = Field(max_length=200)


class ArquivoCatalogo(BaseModel):
    conteudo: str = Field(min_length=1, max_length=2_000_000)


def _exigir_admin(sessao: str | None) -> None:
    if not admin.sessao_valida(sessao):
        raise HTTPException(status_code=401, detail="Entre como administrador para continuar.")


@app.post("/admin/entrar")
def rota_entrar(entrada: Login, resposta: Response) -> dict:
    if not admin.confere(entrada.usuario, entrada.senha):
        # Mesma mensagem para usuário ou senha errados (RF006, fluxo secundário).
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
    resposta.set_cookie(admin.COOKIE, admin.abrir_sessao(), httponly=True,
                        samesite="strict", max_age=admin.DURACAO_SESSAO)
    return {"ok": True}


@app.post("/admin/sair")
def rota_sair(resposta: Response, cheek_sessao: str | None = Cookie(default=None)) -> dict:
    admin.fechar_sessao(cheek_sessao)
    resposta.delete_cookie(admin.COOKIE)
    return {"ok": True}


@app.get("/admin/sessao")
def rota_sessao(cheek_sessao: str | None = Cookie(default=None)) -> dict:
    return {"autenticado": admin.sessao_valida(cheek_sessao)}


@app.post("/admin/importar")
def rota_importar(entrada: ArquivoCatalogo, cheek_sessao: str | None = Cookie(default=None)) -> dict:
    _exigir_admin(cheek_sessao)
    try:
        total = db.importar_texto(conn, entrada.conteudo)
    except db.ErroImportacao as e:
        raise HTTPException(status_code=400, detail=f"Importação recusada. {e}")
    return {"importados": total}


@app.get("/admin/historico")
def rota_historico(tipo: str | None = None, limite: int = 200,
                   cheek_sessao: str | None = Cookie(default=None)) -> list[dict]:
    _exigir_admin(cheek_sessao)
    if tipo not in (None, "chat", "conferencia"):
        raise HTTPException(status_code=400, detail="Tipo deve ser chat ou conferencia.")
    return db.listar_historico(conn, limite=max(1, min(limite, 1000)), tipo=tipo)


@app.get("/")
def pagina_inicial() -> FileResponse:
    return FileResponse(PASTA_STATIC / "index.html")


app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")
