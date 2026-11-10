
import customtkinter as ctk

from backend.database.connection import SessionLocal
from backend.services.auth_service import AuthService
from frontend.ui.styles import colors
from frontend.ui.styles import typography


class LoginPage(ctk.CTkFrame):
    """Login screen for FIDOMEK ONE."""

    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color=colors.BACKGROUND)

        self.on_login_success = on_login_success
        self.password_visible = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_layout()

    def _build_layout(self):
        container = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=colors.BORDER,
        )
        container.grid(row=0, column=0, padx=30, pady=30)

        container.grid_columnconfigure(0, weight=1)

        # Brand
        ctk.CTkLabel(
            container,
            text="FIDOMEK ONE",
            font=(typography.FONT_FAMILY, 27, "bold"),
            text_color=colors.SECONDARY,
        ).grid(row=0, column=0, padx=45, pady=(40, 8))

        ctk.CTkLabel(
            container,
            text="Votre espace de gestion documentaire",
            font=(typography.FONT_FAMILY, 13),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=1, column=0, padx=30, pady=(0, 30))

        # Welcome
        ctk.CTkLabel(
            container,
            text="Bienvenue",
            font=(typography.FONT_FAMILY, 22, "bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=2, column=0, sticky="w", padx=40, pady=(0, 6))

        ctk.CTkLabel(
            container,
            text="Connectez-vous pour accéder à votre espace.",
            font=(typography.FONT_FAMILY, 12),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=3, column=0, sticky="w", padx=40, pady=(0, 24))

        # Email
        ctk.CTkLabel(
            container,
            text="Adresse e-mail",
            font=(typography.FONT_FAMILY, 12, "bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=4, column=0, sticky="w", padx=40, pady=(0, 7))

        self.email_entry = ctk.CTkEntry(
            container,
            width=360,
            height=44,
            placeholder_text="nom@entreprise.ma",
            font=(typography.FONT_FAMILY, 13),
            border_color=colors.BORDER,
            fg_color=colors.SURFACE_ALT,
        )
        self.email_entry.grid(row=5, column=0, padx=40, pady=(0, 18))

        # Password
        ctk.CTkLabel(
            container,
            text="Mot de passe",
            font=(typography.FONT_FAMILY, 12, "bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=6, column=0, sticky="w", padx=40, pady=(0, 7))

        self.password_entry = ctk.CTkEntry(
            container,
            width=360,
            height=44,
            placeholder_text="Votre mot de passe",
            show="*",
            font=(typography.FONT_FAMILY, 13),
            border_color=colors.BORDER,
            fg_color=colors.SURFACE_ALT,
        )
        self.password_entry.grid(row=7, column=0, padx=40, pady=(0, 8))

        self.show_password_var = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(
            container,
            text="Afficher le mot de passe",
            variable=self.show_password_var,
            command=self._toggle_password,
            font=(typography.FONT_FAMILY, 11),
            text_color=colors.TEXT_SECONDARY,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
        ).grid(row=8, column=0, sticky="w", padx=40, pady=(0, 18))

        # Error message
        self.message_label = ctk.CTkLabel(
            container,
            text="",
            font=(typography.FONT_FAMILY, 11),
            text_color=colors.ERROR,
            wraplength=350,
        )
        self.message_label.grid(row=9, column=0, padx=40, pady=(0, 8))

        # Login button
        self.login_button = ctk.CTkButton(
            container,
            text="Se connecter",
            width=360,
            height=46,
            font=(typography.FONT_FAMILY, 13, "bold"),
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=self._login,
        )
        self.login_button.grid(row=10, column=0, padx=40, pady=(0, 25))

        ctk.CTkLabel(
            container,
            text="Accès réservé aux utilisateurs autorisés",
            font=(typography.FONT_FAMILY, 10),
            text_color=colors.TEXT_MUTED,
        ).grid(row=11, column=0, padx=30, pady=(0, 25))

        self.password_entry.bind("<Return>", lambda event: self._login())
        self.email_entry.bind("<Return>", lambda event: self.password_entry.focus_set())

        self.email_entry.focus_set()

    def _toggle_password(self):
        self.password_visible = self.show_password_var.get()
        self.password_entry.configure(
            show="" if self.password_visible else "*"
        )

    def _login(self):
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get()

        self.message_label.configure(text="")

        if not email or not password:
            self.message_label.configure(
                text="Veuillez saisir votre e-mail et votre mot de passe."
            )
            return

        self.login_button.configure(
            state="disabled",
            text="Connexion en cours..."
        )
        self.update_idletasks()

        session = SessionLocal()

        try:
            auth_service = AuthService(session)
            user = auth_service.authenticate(email, password)

            if user is None:
                self.message_label.configure(
                    text="E-mail ou mot de passe incorrect, ou compte désactivé."
                )
                return

            self.on_login_success(user)

        except Exception:
            self.message_label.configure(
                text="Une erreur est survenue. Veuillez réessayer."
            )
            raise

        finally:
            session.close()
            self.login_button.configure(
                state="normal",
                text="Se connecter"
            )
