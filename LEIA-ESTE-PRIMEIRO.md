# LEIA-ESTE-PRIMEIRO

Este projeto é um sistema didático de Controle de Estoque, Vendas e Pedidos (Preparação/Envio) em Python 3.10+, com GUI Tkinter e banco SQLite.

Siga este roteiro rápido:

1) Como rodar o projeto
- (Opcional) Crie um ambiente virtual:
  - Windows: `python -m venv .venv && .venv\Scripts\Activate`
  - Linux/macOS: `python3 -m venv .venv && source .venv/bin/activate`
- (Opcional) Instale extras (ícone/gerador de logo): `pip install -r requirements.txt`
- Execute a aplicação: `python app.py`
- Login: usuário `admin`, senha `admin`.

2) Roteiro de leitura rápido
- Comece por `docs/00_ONDE_COMECAR.md` para entender a ordem dos arquivos e o fluxo de eventos → modelos → banco.
- Em seguida, use `docs/01_ARQUITETURA.md` para ver diagramas (Mermaid) do fluxo “fazer uma venda” e “enviar pedido”.

3) Checklist de entendimento (autoavaliação)
Você deve conseguir explicar:
- Como um clique no botão “Finalizar venda (F5)” gera uma venda em `sales` e, em seguida, um pedido “AGUARDANDO” em `orders`.
- Por que o estoque só é baixado quando o pedido muda para “ENVIADO”.
- Onde ficam as regras de produto (validações, grupo, margem) e como o CRUD conversa com o SQLite.
- Como as telas se atualizam: eventos do Tkinter → chamadas de métodos → consultas e refresh de tabelas.
- Como exportar relatórios (CSV) no formato brasileiro (R$ e vírgula decimal).

Se algum ponto não ficar claro, use o glossário em `docs/02_GLOSSARIO.md`.

Boa leitura e bons estudos!
