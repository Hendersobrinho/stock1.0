# 02 — Glossário

Python
- Módulo: arquivo `.py` importável.
- Pacote: pasta com `__init__.py` (contém módulos).
- Função: bloco reutilizável que recebe parâmetros e retorna valores.
- Classe: molde para criar objetos (instâncias) com dados e métodos.
- Type hint: anotação de tipos para legibilidade e análise estática.

Tkinter
- Frame: contêiner para outros widgets.
- Widget: componente da UI (Label, Entry, Button, Treeview etc.).
- Event: evento do usuário (clique, tecla).
- StringVar/IntVar: variáveis reativas ligadas a widgets.
- bind: associa um evento a uma função handler.
- mainloop: laço principal que processa eventos.

SQLite
- Tabela: estrutura de dados (linhas e colunas) no banco.
- Índice: acelera buscas por colunas.
- Transação: bloco atômico de operações no banco (`with conn:`).
- FK (Foreign Key): integridade referencial entre tabelas.
- CRUD: Create, Read, Update, Delete.

Negócio
- SKU: identificador único de produto.
- Margem: `preço_venda - preço_custo`.
- Markup: `(preço_venda / preço_custo - 1) * 100`.
- Total bruto: soma sem descontos.
- Desconto: redução de preço (R$ ou %).
- Total líquido: bruto - desconto (+ frete quando aplicável).
- SLA: tempo-alvo para concluir uma etapa (ex.: 24h para enviar pedido).
- Status do pedido: AGUARDANDO → PREPARADO → ENVIADO (CANCELADO opcional).
