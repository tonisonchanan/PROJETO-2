"""Servidor do Cheek. Rodar com: uvicorn app.main:app --reload"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import chat, conferencia, db, llm

PASTA_STATIC = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Cheek", description="Assistente de atendimento restrito ao catálogo")
conn = db.conectar()
# CHEEK_LLM=0 desliga o modelo local e usa só o modelo de texto.
gerador = chat.gerador_por_modelo if os.environ.get("CHEEK_LLM") == "0" else llm.gerador_ollama


class Pergunta(BaseModel):
    pergunta: str = Field(min_length=1, max_length=500)


class ItemDigitado(BaseModel):
    texto: str = Field(min_length=1, max_length=200)


@app.post("/chat")
def rota_chat(entrada: Pergunta) -> dict:
    resultado = chat.responder(conn, entrada.pergunta, gerador)
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


@app.get("/")
def pagina_inicial() -> FileResponse:
    return FileResponse(PASTA_STATIC / "index.html")


app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")
