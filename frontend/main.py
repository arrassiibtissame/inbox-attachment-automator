
import customtkinter as ctk

from frontend.ui.components.sidebar import Sidebar
from frontend.ui.pages.dashboard_page import DashboardPage
from frontend.ui.pages.documents_page import DocumentsPage
from frontend.ui.pages.clients_page import ClientsPage
from frontend.ui.pages.settings_page import SettingsPage
from frontend.ui.styles import colors
from frontend.ui.styles.theme import configure_theme
from frontend.ui.pages.splash_screen import SplashScreen


class FidomekOneApp(ctk.CTk):
    """Fenêtre principale de FIDOMEK ONE."""

    def __init__(self):
        configure_theme()
        super().__init__()

        self.title("FIDOMEK ONE | Gestion des documents")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=colors.BACKGROUND)

        # Masquer la fenêtre principale au démarrage.
        self.withdraw()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(
            self,
            on_navigate=self.show_page,
        )
        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0,0),
            pady=0,
        )

        self.content = ctk.CTkFrame(
            self,
            fg_color=colors.BACKGROUND,
            corner_radius=0,
        )
        self.content.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=0,
            pady=0,
        )
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.pages = {
            "dashboard": DashboardPage,
            "documents": DocumentsPage,
            "clients": ClientsPage,
            "settings": SettingsPage,
        }

        self.current_page = None
        self.show_page("dashboard")

        # Créer le splash screen.
        self.splash = SplashScreen(
            self,
            on_complete=self.open_main_window,
        )

    def open_main_window(self):
        """Afficher l'application après le splash screen."""
        self.deiconify()
        self.lift()

    def show_page(self, page_name):
        """Affiche la page choisie dans la barre latérale."""

        page_class = self.pages.get(page_name)

        if page_class is None:
            return

        if self.current_page is not None:
            self.current_page.destroy()

        self.current_page = page_class(self.content)
        self.current_page.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.sidebar.set_active(page_name)


if __name__ == "__main__":
    app = FidomekOneApp()
    app.mainloop()
