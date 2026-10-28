
import customtkinter as ctk

from frontend.ui.components.page_header import PageHeader
from frontend.ui.styles import colors, typography


class ClientsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = PageHeader(
            self,
            title="Clients",
            subtitle="GÃ©rez les sociÃ©tÃ©s clientes du cabinet",
        )
        header.grid(
            row=0, column=0, sticky="ew",
            padx=32, pady=(30, 20)
        )

        # Barre de recherche et bouton d'ajout
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(
            row=1, column=0, sticky="ew",
            padx=32, pady=(0, 18)
        )
        toolbar.grid_columnconfigure(0, weight=1)

        self.search_input = ctk.CTkEntry(
            toolbar,
            placeholder_text="Rechercher une sociÃ©tÃ©...",
            height=40,
            corner_radius=10,
            border_color=colors.BORDER,
            fg_color=colors.SURFACE,
        )
        self.search_input.grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )

        ctk.CTkButton(
            toolbar,
            text="+ Ajouter un client",
            height=40,
            corner_radius=10,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=self.open_add_client_form,
        ).grid(row=0, column=1)

        # Liste des clients
        self.list_frame = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        self.list_frame.grid(
            row=2, column=0, sticky="nsew",
            padx=32, pady=(0, 30)
        )
        self.list_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.list_frame,
            text="SociÃ©tÃ©s clientes",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(
            row=0, column=0, sticky="w",
            padx=22, pady=(22, 12)
        )

        self.empty_message = ctk.CTkLabel(
            self.list_frame,
            text="Aucun client enregistrÃ© pour le moment.",
            font=ctk.CTkFont(size=14),
            text_color=colors.TEXT_SECONDARY,
        )
        self.empty_message.grid(
            row=1, column=0, sticky="nsew",
            padx=20, pady=30
        )

    def open_add_client_form(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Ajouter un client")
        dialog.geometry("420x360")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="Nouveau client",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 18))

        ctk.CTkLabel(
            dialog, text="Nom de la sociÃ©tÃ©",
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", padx=24)

        name_input = ctk.CTkEntry(
            dialog,
            placeholder_text="Ex. SociÃ©tÃ© Exemple SARL",
            height=38,
        )
        name_input.grid(row=2, column=0, sticky="ew", padx=24, pady=(5, 14))

        ctk.CTkLabel(
            dialog, text="Identifiant fiscal (facultatif)",
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=3, column=0, sticky="w", padx=24)

        tax_input = ctk.CTkEntry(
            dialog,
            placeholder_text="Identifiant fiscal",
            height=38,
        )
        tax_input.grid(row=4, column=0, sticky="ew", padx=24, pady=(5, 18))

        message = ctk.CTkLabel(
            dialog, text="", text_color="#C0392B"
        )
        message.grid(row=5, column=0, padx=24)

        def save_client():
            name = name_input.get().strip()

            if not name:
                message.configure(text="Le nom de la sociÃ©tÃ© est obligatoire.")
                return

            # Enregistrement temporaire : SQLite sera ajoutÃ© plus tard.
            print({
                "nom": name,
                "identifiant_fiscal": tax_input.get().strip(),
            })
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text="Valider",
            height=40,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=save_client,
        ).grid(row=6, column=0, sticky="ew", padx=24, pady=(8, 24))

