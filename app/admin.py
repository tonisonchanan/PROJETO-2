"""Acesso administrativo (RF006), importação pela tela (RF001) e histórico (RF005).

Usuário e senha vêm das variáveis de ambiente CHEEK_ADMIN_USUARIO e CHEEK_ADMIN_SENHA.
Nada disso fica no código. Se a senha não for definida, o servidor sorteia uma ao
iniciar e a mostra no terminal, para que a área administrativa nunca fique aberta
com uma senha conhecida.

A sessão é um código aleatório guardado num cookie e vale até o administrador sair
ou o servidor ser reiniciado.
"""
import os
import secrets
import time

USUARIO = os.environ.get("CHEEK_ADMIN_USUARIO", "admin")
SENHA = os.environ.get("CHEEK_ADMIN_SENHA") or ""
SENHA_SORTEADA = not SENHA
if SENHA_SORTEADA:
    SENHA = secrets.token_urlsafe(9)

COOKIE = "cheek_sessao"
DURACAO_SESSAO = 8 * 60 * 60  # um turno de atendimento

_sessoes: dict[str, float] = {}


def aviso_de_inicio() -> str | None:
    if SENHA_SORTEADA:
        return (f"Área administrativa do Cheek: usuário '{USUARIO}', senha '{SENHA}'. "
                "Para fixar a senha, defina CHEEK_ADMIN_SENHA antes de iniciar.")
    return None


def confere(usuario: str, senha: str) -> bool:
    # compare_digest leva o mesmo tempo acertando ou errando, então não dá pistas da senha.
    usuario_ok = secrets.compare_digest(usuario.encode(), USUARIO.encode())
    senha_ok = secrets.compare_digest(senha.encode(), SENHA.encode())
    return usuario_ok and senha_ok


def abrir_sessao() -> str:
    token = secrets.token_urlsafe(32)
    _sessoes[token] = time.time() + DURACAO_SESSAO
    return token


def sessao_valida(token: str | None) -> bool:
    if not token or token not in _sessoes:
        return False
    if _sessoes[token] < time.time():
        del _sessoes[token]
        return False
    return True


def fechar_sessao(token: str | None) -> None:
    if token:
        _sessoes.pop(token, None)
