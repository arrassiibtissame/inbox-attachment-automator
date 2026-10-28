
import customtkinter as ctk

from frontend.ui.components.page_header import PageHeader
from frontend.ui.styles import colors, typography


class DocumentsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # En-tête
        header = PageHeader(
            self,
            title="Documents",
            subtitle="Consultez et gérez les documents reçus",
        )
        header.grid(
            row=0, column=0, sticky="ew",
            padx=32, pady=(30, 20)
        )

        # Recherche
        search_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        search_frame.grid(
            row=1, column=0, sticky="ew",
            padx=32, pady=(0, 18)
        )
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_input = ctk.CTkEntry(
            search_frame,
            placeholder_text="Rechercher un document...",
            height=40,
            corner_radius=10,
            border_color=colors.BORDER,
            fg_color=colors.SURFACE,
            text_color=colors.TEXT_PRIMARY,
        )
        self.search_input.grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )

        self.search_button = ctk.CTkButton(
            search_frame,
            text="Rechercher",
            width=120,
            height=40,
            corner_radius=10,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=self.search_documents,
        )
        self.search_button.grid(row=0, column=1)

        # Zone de la liste
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
            text="Liste des documents",
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
            text=(
                "Aucun document à afficher.\n"
                "Les documents Gmail apparaîtront ici "
                "après l'intégration."
            ),
            font=ctk.CTkFont(size=14),
            text_color=colors.TEXT_SECONDARY,
            justify="center",
        )
        self.empty_message.grid(
            row=1, column=0, sticky="nsew",
            padx=20, pady=30
        )

    def search_documents(self):
        # La recherche sera connectée aux données plus tard.
        query = self.search_input.get().strip()

        if query:
            print(f"Recherche demandée : {query}")
        else:
            print("Aucun terme de recherche saisi.")

