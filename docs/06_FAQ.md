# 06 — FAQ

Erros de import (ModuleNotFoundError)
- Confirme que está dentro da pasta do projeto ao rodar `python app.py`.
- Ative a venv correta (no Windows: `.venv\Scripts\Activate`).

Tkinter não abre
- Em algumas distros Linux é preciso instalar `python3-tk` pelo gerenciador de pacotes.

Encoding/acentos estranhos
- Use `UTF-8` no seu editor e no console.

Banco travado (database is locked)
- Evite abrir dois programas que escrevem no `estoque.db` ao mesmo tempo.
- O projeto já isola a criação de pedido fora da transação da venda.

Ícones não aparecem no Windows
- Gere a logo: `python assets/generate_logo.py`.
- Feche e abra o app; às vezes o Windows cacheia ícones.

Onde estão os dados?
- Arquivo `data/estoque.db`. Use `scripts/check_db.py` para inspecionar rapidamente.
