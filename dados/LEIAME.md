# Catálogos

## catalogo_induprol.csv

Catálogo usado pelo Cheek. São 96 produtos da loja virtual da Induprol Produtos Químicos
(https://induprol.lojaintegrada.com.br/), lidos em 21/10/2026: nome, código (SKU da loja),
descrição, unidade e preço. Produtos com variações de preço, como 1 L e 5 L, viraram um item
por variação, com o sufixo da variação no código (por exemplo `QHYSFYJUZ-1L` e `QHYSFYJUZ-5L`).
Produtos cujo preço não deu para confirmar ficaram de fora.

Os preços são os da loja na data da leitura e podem ter mudado. Para atualizar, gere um CSV
com as mesmas colunas (`codigo,nome,descricao,unidade,preco`) e importe com
`python -m app.importar caminho.csv`. A importação substitui o catálogo inteiro.

## catalogo_amostra.csv

Amostra **fictícia** de 30 itens (códigos `AM001` a `AM030`), montada pela equipe e usada só
nos testes automatizados. Os itens foram escolhidos com nomes parecidos e volumes diferentes
(por exemplo, Desinfetante Lavanda 2 L e 5 L), porque esse tipo de confusão causou o erro de
pedido relatado pela empresa. Ela continua nos testes para que eles não mudem quando o
catálogo real for atualizado.
