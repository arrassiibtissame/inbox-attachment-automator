
import customtkinter as ctk

from frontend.ui.components.document_header import DocumentHeader
from frontend.ui.components.document_statistics import DocumentStatistics
from frontend.ui.components.document_toolbar import DocumentToolbar
from frontend.ui.components.document_card import DocumentCard
from frontend.ui.components.document_preview_panel import DocumentPreviewPanel
from frontend.ui.styles import colors, typography


class DocumentsPage(ctk.CTkFrame):
    """Page de consultation et de gestion des documents."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.documents = [
            {
                "id": 1,
                "name": "Facture_2026_001.pdf",
                "client": "COPAG",
                "type": "PDF",
                "date": "30/10/2026",
                "size": "245 KB",
                "status": "À vérifier",
            },
            {
                "id": 2,
                "name": "Releve_bancaire_octobre.xlsx",
                "client": "Entreprise Atlas",
                "type": "Excel",
                "date": "29/10/2026",
                "size": "180 KB",
                "status": "Classé",
            },
            {
                "id": 3,
                "name": "Declaration_TVA.pdf",
                "client": "Maroc Services",
                "type": "PDF",
                "date": "28/10/2026",
                "size": "320 KB",
                "status": "À vérifier",
            },
            {
                "id": 4,
                "name": "Contrat_prestation.docx",
                "client": "Entreprise Atlas",
                "type": "Word",
                "date": "27/10/2026",
                "size": "95 KB",
                "status": "Classé",
            },
        ]

        self.search_query = ""
        self.selected_filter = "Tous"
        self.document_cards = []

        # En-tête
        self.header = DocumentHeader(self)
        self.header.grid(
            row=0, column=0, sticky="ew",
            padx=typography.PAGE_PADDING, pady=(30, 20),
        )

        # Statistiques
        self.statistics = DocumentStatistics(self)
        self.statistics.grid(
            row=1, column=0, sticky="ew",
            padx=typography.PAGE_PADDING, pady=(0, 20),
        )

        # Recherche et filtres
        self.toolbar = DocumentToolbar(
            self,
            on_search=self.search_documents,
            on_filter=self.filter_documents,
        )
        self.toolbar.grid(
            row=2, column=0, sticky="ew",
            padx=typography.PAGE_PADDING, pady=(0, 20),
        )

        # Titre
        ctk.CTkLabel(
            self,
            text="Documents reçus",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(
            row=3, column=0, sticky="w",
            padx=typography.PAGE_PADDING, pady=(0, 12),
        )

        # Zone principale : liste et panneau latéral
        self.main_area = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.main_area.grid(
            row=4, column=0, sticky="nsew",
            padx=typography.PAGE_PADDING, pady=(0, 25),
        )
        self.main_area.grid_columnconfigure(0, weight=3)
        self.main_area.grid_columnconfigure(1, weight=2)
        self.main_area.grid_rowconfigure(0, weight=1)

        # Liste des documents
        self.list_frame = ctk.CTkScrollableFrame(
            self.main_area,
            fg_color=colors.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=colors.BORDER,
        )
        self.list_frame.grid(
            row=0, column=0, sticky="nsew", padx=(0, 10),
        )
        self.list_frame.grid_columnconfigure(0, weight=1)

        self.empty_message = ctk.CTkLabel(
            self.list_frame,
            text="Aucun document trouvé.",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BODY_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        )

        # Panneau latéral
        self.preview_panel = DocumentPreviewPanel(self.main_area)
        self.preview_panel.grid(
            row=0, column=1, sticky="nsew", padx=(10, 0),
        )

        self.update_statistics()
        self.display_documents()

    def update_statistics(self):
        total = len(self.documents)
        pending = sum(
            document["status"] == "À vérifier"
            for document in self.documents
        )
        classified = sum(
            document["status"] == "Classé"
            for document in self.documents
        )

        self.statistics.update_statistics(
            total, pending, classified
        )

    def search_documents(self, query):
        self.search_query = query.lower()
        self.display_documents()

    def filter_documents(self, filter_name):
        self.selected_filter = filter_name
        self.display_documents()

    def get_filtered_documents(self):
        filtered = self.documents

        if self.search_query:
            filtered = [
                document for document in filtered
                if self.search_query in document["name"].lower()
                or self.search_query in document["client"].lower()
            ]

        if self.selected_filter == "À vérifier":
            filtered = [
                document for document in filtered
                if document["status"] == "À vérifier"
            ]
        elif self.selected_filter == "Classés":
            filtered = [
                document for document in filtered
                if document["status"] == "Classé"
            ]

        return filtered

    def display_documents(self):
        for card in self.document_cards:
            card.destroy()

        self.document_cards.clear()
        self.empty_message.grid_remove()

        filtered_documents = self.get_filtered_documents()

        if not filtered_documents:
            self.empty_message.grid(
                row=0, column=0, pady=40,
            )
            return

        for index, document in enumerate(filtered_documents):
            card = DocumentCard(
                self.list_frame,
                document=document,
                on_details=lambda selected_document=document: self.select_document(
                    selected_document
                ),
            )
            card.grid(
                row=index, column=0, sticky="ew",
                padx=10, pady=(10, 0),
            )
            self.document_cards.append(card)

    def select_document(self, document):
        self.preview_panel.show_document(document)

    def change_document_status(self, document):
        """Modifie le statut d'un document."""
        if document["status"] == "À vérifier":
            document["status"] = "Classé"
        elif document["status"] == "Classé":
            document["status"] = "À vérifier"
        else:
            return

        self.update_statistics()
        self.display_documents()

        if self.preview_panel.current_document is document:
            self.preview_panel.show_document(document)
