# Controle de Estoque e Vendas (Tkinter + SQLite)

Aplicação didática em Python 3.10+ com interface Tkinter e banco de dados SQLite.

## Principais recursos
- Tela de login (usuário padrão: `admin` / `admin`)
- Cadastro de produtos (nome, categoria, preço, quantidade)
- Alterar, excluir e listar produtos
- Registrar vendas (atualização automática do estoque)
- Relatórios simples (quantidade de vendas, receita total, produtos em falta)
- Exportação de relatório em CSV
- Ícone automático (se Pillow estiver instalado)
 - Logo SVG e gerador de PNG/ICO

## Estrutura do projeto
- `app.py` — Inicializa a aplicação e gerencia as abas
- `db.py` — Camada de acesso a dados (SQLite), cria e opera as tabelas
- `utils.py` — Funções utilitárias (hash de senha, validações, CSV)
- `views/` — Telas Tkinter:
  - `views/login_view.py` — Tela de login
  - `views/product_view.py` — CRUD de produtos
  - `views/sales_view.py` — Registro de vendas
  - `views/reports_view.py` — Relatórios e exportação CSV
- `data/` — Pasta criada automaticamente para o banco de dados e arquivos gerados

## Requisitos
- Python 3.10+
- Bibliotecas padrão (Tkinter, sqlite3, csv, hashlib etc.)
- Opcional: Pillow (apenas para geração de ícone)

Opcionalmente instale dependências extras:

```
pip install -r requirements.txt
```

Se não for instalar nada extra, a aplicação funciona com a biblioteca padrão.
Se Pillow estiver instalado, um ícone `data/icon.ico` será gerado e aplicado na janela.

### Logo do programa
- Arquivo vetor: `assets/logo.svg`
- Gerador (Pillow): `python assets/generate_logo.py`
  - Gera `assets/logo.png` (512x512), `assets/logo_small.png` (128x128) e `data/icon.ico` (multi-tamanho)

## Como executar
1. Certifique-se de estar com o Python 3.10+.
2. (Opcional) Crie um ambiente virtual e ative-o.
3. (Opcional) Instale as dependências extras com `pip install -r requirements.txt`.
4. Rode a aplicação:

```
python app.py
```

Ao abrir, use `admin` / `admin` para entrar. O arquivo do banco é criado em `data/estoque.db`.

## Observações didáticas
- O campo `preco` é tratado como preço de venda. O relatório de "lucro" aqui exibe a soma de receitas.
  Para lucro real, adicione no futuro um campo `preco_custo` e calcule `lucro = (preco_venda - preco_custo) * qtd`.
- A senha é armazenada como hash SHA-256 com um SALT estático (didático). Em produção, use um KDF robusto (ex.: bcrypt/argon2) e SALT por usuário.

## Próximos passos sugeridos
- Adicionar preço de custo para relatório de lucro real
- Controle de usuários com perfis (admin/operador) e auditoria
- Buscar/filtrar produtos por nome/categoria na listagem
- Paginação ou busca para listas grandes
- API REST (FastAPI/Flask) para integrações externas
- Emissão de NF-es/boletos e gateway de pagamento (integrações futuras)
