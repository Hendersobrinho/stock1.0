"""
Aplicativo principal (GUI) do sistema de Controle de Estoque e Vendas.

Este arquivo inicializa a aplicação Tkinter, exibe a tela de login e,
após autenticação, apresenta as abas de Produtos, Vendas e Relatórios.

Requisitos: Python 3.10+
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from db import Database
from utils import try_generate_icon
from views.login_view import LoginFrame
from views.product_view import ProductFrame
from views.sales_view import SalesFrame
from views.reports_view import ReportsFrame
from views.fulfillment_view import FulfillmentFrame


class App(tk.Tk):
    """Classe principal da aplicação.

    Responsável por:
    - Instanciar a base de dados
    - Exibir o fluxo de login
    - Criar e gerenciar as abas principais após autenticação
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Controle de Estoque e Vendas")
        self.geometry("1000x640")
        self.minsize(960, 600)

        # Ícone da janela (opcional): usa ícone pré-gerado, ou gera um simples via Pillow
        try:
            # Preferir ícone gerado pelo script (se existir)
            import os, sys
            # Em Windows, definir AppUserModelID ajuda a fixar o ícone na barra de tarefas
            if sys.platform == "win32":
                try:
                    import ctypes  # type: ignore
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("control_stock.app.1.0")
                except Exception:
                    pass

            ico = os.path.abspath(os.path.join("data", "icon.ico"))
            if os.path.exists(ico):
                self.iconbitmap(ico)  # type: ignore[arg-type]
            else:
                icon_path = try_generate_icon()
                if icon_path:
                    self.iconbitmap(os.path.abspath(str(icon_path)))  # type: ignore[arg-type]
            # Fallback PNG (todas as plataformas): carrega múltiplos tamanhos para melhor nitidez
            try:
                from PIL import Image, ImageTk  # type: ignore
                sizes = [16, 24, 32, 48, 64, 128, 256]
                self._icon_photos = []
                for s in sizes:
                    path = os.path.abspath(os.path.join("assets", f"logo_{s}.png"))
                    if not os.path.exists(path):
                        continue
                    im = Image.open(path).convert("RGBA")
                    self._icon_photos.append(ImageTk.PhotoImage(im))
                if self._icon_photos:
                    self.iconphoto(True, *self._icon_photos)
            except Exception:
                # Fallback sem Pillow
                png = os.path.abspath(os.path.join("assets", "logo_small.png"))
                if os.path.exists(png):
                    try:
                        self._icon_photo = tk.PhotoImage(file=png)
                        self.iconphoto(True, self._icon_photo)
                    except Exception:
                        pass
        except Exception:
            # Ícone é opcional; se falhar, seguimos sem definir
            pass

        # Barra superior com logo e título
        self._build_header()

        # Instância central do banco de dados
        self.db = Database("data/estoque.db")

        # Container principal; iniciamos com a tela de login
        self._main_container = ttk.Frame(self)
        self._main_container.pack(fill=tk.BOTH, expand=True)

        self.login_frame: LoginFrame | None = None
        self.notebook: ttk.Notebook | None = None

        # Primeiro cria a barra de menu
        self._build_menubar()

        # Exibe a tela de login somente agora (menus e atributos já prontos)
        self.show_login()

    def _build_header(self) -> None:
        """Cria uma barra superior com a logo e o título do sistema."""
        import os
        bar = ttk.Frame(self)
        bar.pack(side=tk.TOP, fill=tk.X)

        # Carrega a logo para a barra com melhor ajuste ao DPI
        self._logo_img = None
        # Estima fator de escala (DPI) do Tk para escolher tamanho adequado
        try:
            dpi_scale = float(self.winfo_fpixels('1i')) / 72.0
        except Exception:
            dpi_scale = 1.0
        target = 32
        size = 32
        if dpi_scale >= 1.75:
            size = 48
        elif dpi_scale >= 1.25:
            size = 40
        # Seleciona arquivo mais próximo
        candidates = [32, 40, 48, 64]
        pick = min(candidates, key=lambda s: abs(s - size))
        try:
            from PIL import Image, ImageTk  # type: ignore
            p = os.path.join("assets", f"logo_{pick if pick in (32,48,64) else 32}.png")
            if not os.path.exists(p):
                p = os.path.join("assets", "logo_32.png")
            if os.path.exists(p):
                im = Image.open(p).convert("RGBA")
                self._logo_img = ImageTk.PhotoImage(im)
                ttk.Label(bar, image=self._logo_img).pack(side=tk.LEFT, padx=(10, 8), pady=6)
        except Exception:
            p = os.path.join("assets", "logo_32.png")
            if os.path.exists(p):
                self._logo_img = tk.PhotoImage(file=p)
                ttk.Label(bar, image=self._logo_img).pack(side=tk.LEFT, padx=(10, 8), pady=6)

        ttk.Label(bar, text="Controle de Estoque e Vendas", font=("Segoe UI", 12, "bold")).pack(
            side=tk.LEFT, pady=6
        )

        # (login é mostrado no final do __init__ após menus/atributos)

    def _build_menubar(self) -> None:
        """Cria a barra de menu da aplicação."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        self.menu_sistema = tk.Menu(menubar, tearoff=0)
        self.menu_sistema.add_command(label="Sair", command=self.quit)
        menubar.add_cascade(label="Sistema", menu=self.menu_sistema)

        self.menu_sessao = tk.Menu(menubar, tearoff=0)
        self.menu_sessao.add_command(label="Logout", command=self.logout, state=tk.DISABLED)
        menubar.add_cascade(label="Sessão", menu=self.menu_sessao)

    def show_login(self) -> None:
        """Exibe a tela de login, destruindo a interface principal se existir."""
        # Esconde/destrói as abas se elas existirem
        if self.notebook is not None:
            self.notebook.destroy()
            self.notebook = None
        # Desabilita opção de logout até logar
        self.menu_sessao.entryconfig("Logout", state=tk.DISABLED)

        # Cria e mostra o frame de login
        self.login_frame = LoginFrame(self._main_container, self.db, on_success=self._on_login_success)
        self.login_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

    def _on_login_success(self, username: str) -> None:
        """Callback chamado após login bem-sucedido.

        Troca a tela de login pelas abas principais.
        """
        if self.login_frame is not None:
            self.login_frame.destroy()
            self.login_frame = None

        # Habilita opção de logout
        self.menu_sessao.entryconfig("Logout", state=tk.NORMAL)

        # Cria notebook com as principais funcionalidades
        self.notebook = ttk.Notebook(self._main_container)

        # Abas: Produtos, Vendas, Pedidos, Relatórios
        self.products_tab = ProductFrame(self.notebook, self.db)
        self.sales_tab = SalesFrame(self.notebook, self.db)
        self.fulfillment_tab = FulfillmentFrame(self.notebook, self.db)
        self.reports_tab = ReportsFrame(self.notebook, self.db)

        self.notebook.add(self.products_tab, text="Produtos")
        self.notebook.add(self.sales_tab, text="Vendas")
        self.notebook.add(self.fulfillment_tab, text="Pedidos")
        self.notebook.add(self.reports_tab, text="Relatórios")

        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Feedback rápido
        messagebox.showinfo("Bem-vindo", f"Login efetuado como: {username}")

    def logout(self) -> None:
        """Efetua logout retornando à tela de login."""
        resposta = messagebox.askyesno("Logout", "Deseja encerrar a sessão atual?")
        if not resposta:
            return
        self.show_login()


if __name__ == "__main__":
    # Inicia a aplicação Tkinter
    app = App()
    app.mainloop()
