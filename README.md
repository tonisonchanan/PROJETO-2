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

O catálogo em `dados/catalogo_amostra.csv` é uma **amostra fictícia montada pela equipe**,
não o catálogo da Induprol. Veja `dados/LEIAME.md`.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.importar dados/catalogo_amostra.csv
uvicorn app.main:app --reload
```

Abra http://localhost:8000.

### Modelo de linguagem local (opcional)

O chat usa um modelo de código aberto rodando no próprio computador pelo [Ollama](https://ollama.com),
sem API paga e sem chave. O modelo só redige a resposta a partir dos itens que a busca recuperou.

```bash
ollama pull llama3.2:3b            # uma vez
ollama serve                        # se ainda não estiver rodando
```

Variáveis opcionais: `CHEEK_OLLAMA_MODELO` (padrão `llama3.2:3b`), `CHEEK_OLLAMA_URL`
(padrão `http://localhost:11434`), `CHEEK_OLLAMA_TEMPO` (segundos, padrão 30) e `CHEEK_LLM=0`
para desligar o modelo.

Se o Ollama não estiver rodando, demorar demais, ou se a resposta citar código ou preço
que não estão nos itens recuperados, o Cheek descarta o texto do modelo e responde com o
modelo de texto montado direto do catálogo. Perguntas fora do catálogo e perguntas de
segurança nunca chegam ao modelo. A documentação automática das rotas fica em http://localhost:8000/docs.

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
  texto.py        normalização de texto, medidas (5 L, 500 ml) e palavras ignoradas
  conferencia.py  conferência de item por busca aproximada (RF004)
  busca.py        recuperação de itens para o chat (RF002)
  chat.py         resposta, recusa (RF003) e bloqueio de perguntas de segurança
  llm.py          redação da resposta pelo modelo local (Ollama), com conferência de código e preço
dados/            catálogo de amostra
static/           página web (HTML, CSS e JavaScript)
tests/            testes automatizados (pytest)
```

## O que ainda falta

- Rota de importação de catálogo com login de administrador (hoje a importação é só pela linha de comando).
- Tela de consulta do histórico (o histórico já é gravado na tabela `historico`).
