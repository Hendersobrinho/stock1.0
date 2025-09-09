# 10 — Palavras Reservadas do Python (explicadas como professor)

Este guia explica as palavras reservadas (keywords) e construções usadas neste projeto, com exemplos.

Conceito rápido
- Palavras reservadas: nomes que o Python usa para a própria linguagem. Não podem ser usados como nomes de variáveis.
- Exemplos: `def`, `class`, `if`, `else`, `try`, `except`, `with`, `return`, `from`, `import`, `for`, `in`, `as`, `lambda`, `pass`, `yield` etc.

Palavras reservadas usadas aqui

- `def` — define uma função.
  - Ex.: `def _finalize(self) -> None:` cria um método que finaliza a venda.
- `class` — define uma classe.
  - Ex.: `class SalesFrame(ttk.Frame):` define um Frame do Tkinter para a Tela de Vendas.
- `return` — encerra a função e devolve um valor.
  - Ex.: `return sale_id` em `create_sale` devolve o ID da venda.
- `if` / `elif` / `else` — controle condicional.
  - Ex.: bloquear quando `qty <= 0` ou quando não há seleção de produto.
- `for` / `in` — laços de repetição.
  - Ex.: somar subtotais para calcular total bruto/desconto/líquido.
- `try` / `except` — tratamento de exceções.
  - Ex.: ao exportar CSV, capturamos exceções para mostrar mensagens amigáveis.
- `with` — gerencia contexto (fecha recursos automaticamente).
  - Ex.: `with closing(self._connect()) as conn, conn:` abre uma conexão SQLite e garante o commit/rollback automático.
- `from` / `import` — importa módulos e símbolos.
  - Ex.: `from utils.formatting import br_money` para usar formatação BRL.
- `as` — renomeia ou dá um alias durante import/contexto.
  - Ex.: `import tkinter as tk` abrevia o módulo tkinter para `tk`.
- `pass` — marcador de “não fazer nada” (não é muito usado aqui).
- `lambda` — cria uma função anônima curta (usado nos binds do Tkinter para adaptar a assinatura).

Construções úteis da stdlib

- `dataclass` (módulo dataclasses) — gera classes simples com campos.
  - Ex.: `@dataclass class SaleItemInput: ...` cria uma estrutura imutável para itens da venda.
- `contextlib.closing` — fecha objetos ao sair do bloco `with`.
  - Ex.: garante fechamento da conexão (conn.close()).
- `typing` — tipos para legibilidade: `list[str]`, `Optional[int]`, `dict[str, Any]`.
- `Decimal` (módulo decimal) — números com ponto fixo (dinheiro) e arredondamento controlado.

Exemplo comentado (trecho simplificado de create_sale)

```python
with closing(self.db._connect()) as conn:          # with: abre e garante que conn será fechada
    for it in items:                               # for: percorre cada item
        if it.qty <= 0:                            # if: valida quantidade positiva
            raise ValueError("Quantidade inválida")
        # ... valida desconto e estoque ...

# Cálculo com Decimal e arredondamento half-up (ver utils/formatting.round2)
subtotal_gross = round2(ug * q)                    # subtotal bruto = preço * quantidade
discount_value = round2(subtotal_gross * dperc)    # valor do desconto = subtotal * %
subtotal_net   = round2(subtotal_gross - discount_value)
```

Dicas de estudo
- Leia o código com este guia ao lado: identifique cada palavra reservada e pergunte “o que ela faz aqui?”.
- Procure por `with` e tente explicar por que é importante em operações de banco.
- Use `docs/04_TKINTER.md` para entender como `bind`, `command` e variáveis (`StringVar`) funcionam.
