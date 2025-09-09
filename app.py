"""
Aplicativo principal (GUI) do sistema de Controle de Estoque e Vendas.

Inicializa a aplicação Tkinter, exibe a tela de login e, após autenticação,
apresenta as abas de Produtos, Vendas, Pedidos e Relatórios.

Requisitos: Python 3.10+
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from db import Database
# Removido: geração automática de ícone; usamos ativos fixos em assets
from views.login_view import LoginFrame
from views.product_view import ProductFrame
from views.sales_view import SalesFrame
from views.reports_view import ReportsFrame
from views.fulfillment_view import FulfillmentFrame


class App(tk.Tk):
    """Classe principal da aplicação."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Controle de Estoque e Vendas")
        self.geometry("1000x640")
        self.minsize(960, 600)

        # Ícone da janela (GUI):
        # - Windows: tenta aplicar um .ico (barra de título / taskbar) via iconbitmap.
        # - Todas as plataformas: aplica PNG via iconphoto (suporta multi-tamanho com Pillow).
        # - A logo no cabeçalho também reutiliza o mesmo PNG, redimensionado conforme DPI.
        try:
            # Em Windows, definir AppUserModelID ajuda a fixar o ícone na barra de tarefas
            if sys.platform == "win32":
                try:
                    import ctypes  # type: ignore
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                        "control_stock.app.1.0"
                    )
                except Exception:
                    pass

            # 1) Se existir ICO, aplica (melhor integração com taskbar do Windows)
            ico_candidates = [
                os.path.abspath(os.path.join("assets", "icon.ico")),
                os.path.abspath(os.path.join("assets", "logo.ico")),
                os.path.abspath(os.path.join("data", "icon.ico")),
            ]
            ico = next((p for p in ico_candidates if os.path.exists(p)), None)
            if ico:
                try:
                    self.iconbitmap(ico)  # type: ignore[arg-type]
                except Exception:
                    pass
            # Se nenhum ICO existir, seguimos apenas com PNG via iconphoto

            # 2) Aplica PNG base em diferentes tamanhos (iconphoto)
            base_png = os.path.abspath(os.path.join("assets", "logo.png"))
            if os.path.exists(base_png):
                try:
                    from PIL import Image, ImageTk  # type: ignore
                    sizes = [16, 24, 32, 48, 64, 128, 256]
                    base_img = Image.open(base_png).convert("RGBA")
                    self._icon_photos = [
                        ImageTk.PhotoImage(base_img.copy().resize((s, s))) for s in sizes
                    ]
                    self.iconphoto(True, *self._icon_photos)
                except Exception:
                    # Fallback sem Pillow: usa a própria imagem
                    try:
                        self._icon_photo = tk.PhotoImage(file=base_png)
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
        """Cria barra superior com logo e título."""
        dark_bg = "#2B2B2B"  # cinza escuro para a barra
        text_fg = "#FFFFFF"  # fonte clara para bom contraste
        bar = tk.Frame(self, bg=dark_bg, highlightthickness=0, bd=0)
        bar.pack(side=tk.TOP, fill=tk.X)

        # Carrega a logo com melhor ajuste ao DPI
        self._logo_img = None
        # Estima fator de escala (DPI) do Tk para escolher tamanho adequado
        try:
            dpi_scale = float(self.winfo_fpixels("1i")) / 72.0
        except Exception:
            dpi_scale = 1.0
        size = 32
        if dpi_scale >= 1.75:
            size = 48
        elif dpi_scale >= 1.25:
            size = 40

        candidates = [32, 40, 48, 64]
        pick = min(candidates, key=lambda s: abs(s - size))
        base_png = os.path.join("assets", "logo.png")
        try:
            from PIL import Image, ImageTk  # type: ignore
            if os.path.exists(base_png):
                im = Image.open(base_png).convert("RGBA")
                if im.width != pick or im.height != pick:
                    im = im.resize((pick, pick))
                self._logo_img = ImageTk.PhotoImage(im)
                tk.Label(bar, image=self._logo_img, bg=dark_bg, bd=0).pack(
                    side=tk.LEFT, padx=(10, 8), pady=6
                )
        except Exception:
            # Fallback sem Pillow
            if os.path.exists(base_png):
                try:
                    self._logo_img = tk.PhotoImage(file=base_png)
                    tk.Label(bar, image=self._logo_img, bg=dark_bg, bd=0).pack(
                        side=tk.LEFT, padx=(10, 8), pady=6
                    )
                except Exception:
                    pass

        tk.Label(
            bar,
            text="Controle de Estoque e Vendas",
            font=("Segoe UI", 12, "bold"),
            fg=text_fg,
            bg=dark_bg,
        ).pack(side=tk.LEFT, pady=6)

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
