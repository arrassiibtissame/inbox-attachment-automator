
import customtkinter as ctk

from frontend.ui.components.sidebar import Sidebar
from frontend.ui.pages.dashboard_page import DashboardPage
from frontend.ui.pages.documents_page import DocumentsPage
from frontend.ui.pages.clients_page import ClientsPage
from frontend.ui.pages.settings_page import SettingsPage
from frontend.ui.pages.splash_screen import SplashScreen
from frontend.ui.pages.login_page import LoginPage
from frontend.ui.styles import colors
from frontend.ui.styles.theme import configure_theme
from frontend.ui.pages.employees_page import EmployeesPage

from backend.gmail_monitor import GmailMonitor


class FidomekOneApp(ctk.CTk):
    """Fenêtre principale de FIDOMEK ONE."""

    def __init__(self):
        configure_theme()
        super().__init__()

        self.title("FIDOMEK ONE | Gestion des documents")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=colors.BACKGROUND)

        self.withdraw()

        self.current_user = None
        self.gmail_monitor = GmailMonitor()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Barre latérale
        self.sidebar = Sidebar(
            self,
            on_navigate=self.show_page,
            current_user=None,
            on_logout=self.logout,
        )
        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        # Zone principale
        self.content = ctk.CTkFrame(
            self,
            fg_color=colors.BACKGROUND,
            corner_radius=0,
        )
        self.content.grid(
            row=0,
            column=1,
            sticky="nsew",
        )
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Classes des pages disponibles
        self.page_classes = {
            "dashboard": DashboardPage,
            "documents": DocumentsPage,
            "clients": ClientsPage,
            "employees": EmployeesPage,
            "settings": SettingsPage,
        }

        # Les pages seront créées au premier accès.
        self.page_instances = {}
        self.current_page = None

        # Masquer l'application jusqu'à l'authentification.
        self.sidebar.grid_remove()
        self.content.grid_remove()

        # Écran de connexion
        self.login_page = LoginPage(
            self,
            on_login_success=self.on_login_success,
        )
        self.login_page.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="nsew",
        )
        self.login_page.grid_remove()

        # Splash Screen
        self.splash = SplashScreen(
            self,
            on_complete=self.open_main_window,
        )

        self.protocol("WM_DELETE_WINDOW", self.on_close)





    def create_page(self, page_name):
        """Créer une page uniquement lors de son premier accès."""

        if page_name in self.page_instances:
            return self.page_instances[page_name]

        page_class = self.page_classes.get(page_name)

        if page_class is None:
            return None

        if page_name == "settings":
            page = page_class(
                self.content,
                gmail_monitor=self.gmail_monitor,
            )
        elif page_name == "clients" or page_name == "employees":
            page = page_class(
                self.content,
                current_user=self.current_user,
            )
        else:
            page = page_class(self.content)

        page.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        page.grid_remove()

        self.page_instances[page_name] = page

        return page

    def open_main_window(self):
        """Afficher la connexion après le Splash Screen."""

        self.deiconify()
        self.lift()
        self.login_page.grid()

    def on_login_success(self, user):
        """Afficher l'application après authentification."""

        self.current_user = user
        self.sidebar.set_user(user)
        self.login_page.grid_remove()

        self.sidebar.grid()
        self.content.grid()

        self.show_page("dashboard")

        self.lift()



    def show_page(self, page_name):
        """Afficher une page, en la créant si nécessaire."""

        # Vérifier que l'utilisateur est connecté.
        if self.current_user is None:
            return

        # La gestion des employés est réservée à l'administrateur.
        user_role = getattr(
            self.current_user.role,
            "value",
            self.current_user.role,
        )

        if page_name == "employees" and user_role != "ADMIN":
            return

        page = self.create_page(page_name)

        if page is None:
            return

        if self.current_page is not None:
            self.current_page.grid_remove()

        page.grid()

        self.current_page = page

        self.sidebar.set_active(page_name)

    def logout(self):
        """Déconnecter l'utilisateur et revenir à l'écran de connexion."""

        if self.current_page is not None:
            self.current_page.grid_remove()
            self.current_page = None

        self.current_user = None

        # Réinitialiser le profil et la navigation
        self.sidebar.set_user(None)

        # Masquer l'interface principale
        self.sidebar.grid_remove()
        self.content.grid_remove()

        # Détruire les pages mises en cache pour éviter
        # qu'un autre utilisateur récupère les données précédentes
        for page in self.page_instances.values():
            page.destroy()

        self.page_instances.clear()

        # Réinitialiser le formulaire de connexion
        self.login_page.email_entry.delete(0, "end")
        self.login_page.password_entry.delete(0, "end")
        self.login_page.message_label.configure(text="")

        # Afficher l'écran de connexion
        self.login_page.grid()
        self.login_page.lift()
        self.login_page.email_entry.focus_set()
    def on_close(self):
        """Arrêter Gmail avant de fermer la fenêtre."""

        self.gmail_monitor.stop()
        self._wait_for_gmail_shutdown()

    def _wait_for_gmail_shutdown(self):
        """Attendre la fin du thread Gmail sans bloquer l'interface."""

        if self.gmail_monitor.is_alive:
            self.after(100, self._wait_for_gmail_shutdown)
        else:
            self.destroy()


if __name__ == "__main__":
    app = FidomekOneApp()
    app.mainloop()
