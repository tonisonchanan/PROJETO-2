# Cheek

Assistente de atendimento para pequeno comércio, desenvolvido no Projeto Integrador II
(ADS, UNESC Virtual) com estudo de caso na Induprol Produtos Químicos.

Esta é a primeira versão do MVP. Ela tem duas telas:

- **Chat do cliente** (`POST /chat`): busca no catálogo os itens ligados à pergunta e responde só com eles.
  Se nada for encontrado, recusa sem inventar. Perguntas de segurança química (mistura, ingestão,
  contato com olhos ou pele) nunca são respondidas e o cliente é orientado a seguir o rótulo e a FISPQ.
- **Conferir item** (`POST /conferir-item`): o atendente digita o item do pedido e recebe até três
  candidatos do catálogo, com o volume conferido. Usa busca aproximada (rapidfuzz), sem modelo de linguagem,
  para que o resultado seja sempre o mesmo para a mesma entrada.

O catálogo em `dados/catalogo_induprol.csv` tem 96 produtos da loja virtual da Induprol
(induprol.lojaintegrada.com.br), com nome, código (SKU da loja), descrição e preço lidos em 21/10/2026.
Ficaram de fora os produtos sem preço confirmado. Veja `dados/LEIAME.md`.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.importar dados/catalogo_induprol.csv
uvicorn app.main:app --reload
```

Abra http://localhost:8000. A documentação automática das rotas fica em http://localhost:8000/docs.

### Área administrativa

A aba **Administração** pede usuário e senha (RF006) e libera a importação do catálogo por arquivo CSV
(RF001) e a lista do histórico de conversas e conferências (RF005). Usuário e senha vêm das variáveis
de ambiente `CHEEK_ADMIN_USUARIO` (padrão `admin`) e `CHEEK_ADMIN_SENHA`. Se a senha não for definida,
o servidor sorteia uma ao iniciar e a mostra no terminal.

```bash
export CHEEK_ADMIN_SENHA='escolha-uma-senha'   # no Windows: set CHEEK_ADMIN_SENHA=escolha-uma-senha
```

## Testes

```bash
pytest -q
```

## Estrutura

```
app/
  main.py         rotas FastAPI e página inicial
  db.py           banco SQLite: catálogo, índice de busca (FTS5) e histórico; importação de CSV
  importar.py     importação do catálogo pela linha de comando
  admin.py        login do administrador e sessão (RF006)
  texto.py        normalização de texto, medidas (5 L, 500 ml) e palavras ignoradas
  conferencia.py  conferência de item por busca aproximada (RF004)
  busca.py        recuperação de itens para o chat (RF002)
  chat.py         resposta, recusa (RF003) e bloqueio de perguntas de segurança
  llm.py          redação opcional pelo modelo de linguagem, com conferência da resposta
dados/            catálogo da Induprol e amostra fictícia usada nos testes
static/           página web (HTML, CSS e JavaScript)
tests/            testes automatizados (pytest)
experimentos/     perguntas de teste e script que as roda
```

## Modelo de linguagem (opcional)

Com a variável `ANTHROPIC_API_KEY` definida, o chat pede ao modelo `claude-opus-5-5` (troque com
`CHEEK_LLM_MODELO`) que redija a resposta usando só os itens que a busca recuperou. Sem a chave, o chat
responde com o texto montado direto do catálogo. A resposta do modelo é descartada, e vale o texto montado,
quando demora mais que 10 segundos (`CHEEK_LLM_TEMPO`), quando a API falha ou recusa, ou quando o texto cita
código que não foi recuperado ou preço diferente do catálogo. Se a busca não acha nada, o modelo nem é chamado.

```bash
export ANTHROPIC_API_KEY='sua-chave'   # no Windows: set ANTHROPIC_API_KEY=sua-chave
```

A chave nunca vai para o código nem para o repositório.

## Experimentos

`python -m experimentos.rodar` roda as 22 perguntas de `experimentos/perguntas_teste.csv` contra o catálogo
real e compara com o resultado esperado (`--md` gera a tabela em Markdown).

## Trabalhos futuros

- Atendimento pelo WhatsApp.
- Integração com o sistema de nota fiscal e boleto da empresa.
- Banco PostgreSQL e hospedagem, se o Cheek sair do computador local.
