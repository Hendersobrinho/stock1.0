# 05 — Testes Manuais

1) Cadastro de produto
- Produtos → preencha SKU, Nome, Categoria, Grupo, Custo, Venda, Estoque, Mínimo.
- Salve. Deve aparecer na lista com a linha em vermelho claro se Estoque < Mínimo.

2) Venda com desconto (item e geral)
- Vendas → busque produto; dê duplo-clique na sugestão; informe Qtd e Desc.% e adicione.
- (Opcional) Aplique desconto geral %; confirme recálculo dos itens.
- Finalize (F5). Mensagem de sucesso + navega para “Pedidos”.

3) Estoque insuficiente
- Em Vendas, tente vender quantidade maior que o estoque → deve bloquear com mensagem clara.

4) Relatórios
- Defina período (ex.: Hoje) e clique “Aplicar”.
- Exporte “Vendas (resumo)” e “Pedidos (resumo)”.
- Abra o CSV e confira numeração BR (vírgula decimal).

5) Preparação/Envio de pedidos
- Em “Pedidos”, selecione o novo pedido.
- Ctrl+Enter para avançar: AGUARDANDO → PREPARADO → ENVIADO (baixa estoque).
- Del cancela quando no início do fluxo.

6) Ajuste de estoque
- Produtos → selecione um item → Ajustar Estoque → informe +5 ou -3; veja a atualização.
