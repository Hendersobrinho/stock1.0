# 07 — Erros Comuns

Mensagem: `ModuleNotFoundError: No module named 'utils.formatting'`
- Causa: arquivo `utils.py` conflitando com pacote `utils/`.
- Solução: garantir que existe a pasta `utils/` com `__init__.py` e remover `utils.py` antigo.

Mensagem: `database is locked`
- Causa: duas transações de escrita simultâneas em SQLite.
- Solução: criar o pedido fora da transação de venda (já implementado) e evitar múltiplos writers.

Mensagem: `TclError` ao carregar imagens
- Causa: caminho incorreto ou falta de Pillow.
- Solução: gere a logo e verifique caminhos; Pillow é opcional.

Linhas somem na Treeview
- Causa: não atualizar a tabela após operação.
- Solução: chamar `refresh_table()` e atualizar os `StringVar`/labels conforme necessário.
