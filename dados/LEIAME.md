# Catálogo de amostra

O arquivo `catalogo_amostra.csv` foi montado pela equipe para desenvolver e testar o Cheek.
Ele **não** é o catálogo da Induprol Produtos Químicos: nomes, códigos (prefixo `AM`), descrições
e preços são fictícios e servem só para exercitar a busca e a conferência de itens.

Os itens foram escolhidos de propósito com nomes parecidos e volumes diferentes
(por exemplo, Desinfetante Lavanda 2 L e 5 L), porque é exatamente esse tipo de confusão
que causou o erro de pedido relatado pela empresa.

Quando a Induprol ceder o catálogo real, basta gerar um CSV com as mesmas colunas
(`codigo,nome,descricao,unidade,preco`) e importar com `python -m app.importar caminho.csv`.
