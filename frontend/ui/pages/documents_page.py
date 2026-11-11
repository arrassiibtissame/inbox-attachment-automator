
import customtkinter as ctk
import os
from pathlib import Path
from tkinter import messagebox

from backend.database.connection import SessionLocal
from backend.services.dashboard_service import DashboardService

from frontend.ui.components.document_header import DocumentHeader
from frontend.ui.components.document_statistics import DocumentStatistics
from frontend.ui.components.document_toolbar import DocumentToolbar
from frontend.ui.components.document_card import DocumentCard
from frontend.ui.components.document_preview_panel import DocumentPreviewPanel
from frontend.ui.styles import colors, typography


class DocumentsPage(ctk.CTkFrame):
    """Page de consultation et de gestion des documents."""

    REFRESH_INTERVAL = 30000
    PAGE_SIZE = 20

    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.current_user = current_user
        self.documents = []
        self.search_query = ""
        self.selected_filter = "Tous"
        self.document_cards = []
        self._refresh_job = None
        self.current_page = 0
        self.selected_dashboard_ids = None
        self.selected_dashboard_title = None

        # En-tête
        self.header = DocumentHeader(self)
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=typography.PAGE_PADDING,
            pady=(30, 20),
        )

        # Statistiques
        self.statistics = DocumentStatistics(self)
        self.statistics.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=typography.PAGE_PADDING,
            pady=(0, 20),
        )

        # Recherche et filtres
        self.toolbar = DocumentToolbar(
            self,
            on_search=self.search_documents,
            on_filter=self.filter_documents,
        )
        self.toolbar.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=typography.PAGE_PADDING,
            pady=(0, 20),
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
            row=3,
            column=0,
            sticky="w",
            padx=typography.PAGE_PADDING,
            pady=(0, 12),
        )

        # Zone principale
        self.main_area = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.main_area.grid(
            row=4,
            column=0,
            sticky="nsew",
            padx=typography.PAGE_PADDING,
            pady=(0, 25),
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
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
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

                # Navigation entre les pages de documents
        self.pagination_frame = ctk.CTkFrame(
            self.list_frame,
            fg_color="transparent",
        )

        self.previous_button = ctk.CTkButton(
            self.pagination_frame,
            text="← Précédent",
            width=100,
            command=self.previous_page,
        )
        self.previous_button.grid(row=0, column=0, padx=8)

        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Page 1 / 1",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        )
        self.page_label.grid(row=0, column=1, padx=8)

        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text="Suivant →",
            width=100,
            command=self.next_page,
        )
        self.next_button.grid(row=0, column=2, padx=8)

        # Panneau latéral
        self.preview_panel = DocumentPreviewPanel(self.main_area)
        self.preview_panel.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0),
        )

        # Chargement initial
        self.refresh_documents()

        # Actualisation automatique
        self._schedule_refresh()

    def refresh_documents(self):
        """Actualiser la liste depuis SQLite."""

        try:
            with SessionLocal() as session:
                rows = DashboardService(session).get_documents(
                    self.current_user
                )

            self.documents = []
            for row in rows:
                received_at = row.get("date")
                if received_at:
                    date_text = received_at.strftime("%d/%m/%Y %H:%M")
                else:
                    date_text = "Date inconnue"

                size_bytes = row.get("size_bytes") or 0
                if size_bytes >= 1024 * 1024:
                    size_text = f"{size_bytes / (1024 * 1024):.1f} MB"
                elif size_bytes >= 1024:
                    size_text = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_text = f"{size_bytes} octets"

                status = (
                    "Classé"
                    if row.get("status") == "CLASSIFIED"
                    else "À vérifier"
                )

                self.documents.append({
                    "document_id": row.get("document_id"),
                    "file_id": row.get("file_id"),
                    "name": row.get("name") or "Document sans nom",
                    "client": row.get("client_name") or "Non attribué",
                    "type": row.get("type") or "Autre",
                    "date": date_text,
                    "status": status,
                    "path": row.get("path"),
                    "size": size_text,
                    "source": row.get("source"),
                })

            self.update_statistics()
            self.display_documents()

        except Exception as error:
            print(
                f"Erreur lors du chargement des documents : {error}"
            )

    def _schedule_refresh(self):
        """Programmer la prochaine actualisation."""

        self._refresh_job = self.after(
            self.REFRESH_INTERVAL,
            self._refresh_documents_and_schedule,
        )

    def _refresh_documents_and_schedule(self):
        self.refresh_documents()
        self._schedule_refresh()

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
            total,
            pending,
            classified,
        )

    def search_documents(self, query):
        self.search_query = query.lower()
        self.current_page = 0
        self.display_documents()

    def filter_documents(self, filter_name):
        self.selected_filter = filter_name
        self.current_page = 0
        self.display_documents()

    def apply_dashboard_filter(self, document_ids, title):
        """Afficher uniquement les documents d'une cat?gorie du tableau de bord."""

        self.search_query = ""
        self.toolbar.search_entry.delete(0, "end")
        self.toolbar.set_filter("Tous")

        self.selected_dashboard_ids = set(document_ids)
        self.selected_dashboard_title = title
        self.current_page = 0
        self.display_documents()

    def clear_dashboard_filter(self):
        """Retirer le filtre temporaire du tableau de bord."""

        self.selected_dashboard_ids = None
        self.selected_dashboard_title = None
        self.current_page = 0

    def get_filtered_documents(self):
        filtered = self.documents

        if self.selected_dashboard_ids is not None:
            filtered = [
                document
                for document in filtered
                if document.get("document_id") in self.selected_dashboard_ids
            ]

        if self.search_query:
            filtered = [
                document
                for document in filtered
                if self.search_query in document["name"].lower()
                or self.search_query in document["client"].lower()
            ]

        if self.selected_filter == "À vérifier":
            filtered = [
                document
                for document in filtered
                if document["status"] == "À vérifier"
            ]

        elif self.selected_filter == "Classés":
            filtered = [
                document
                for document in filtered
                if document["status"] == "Classé"
            ]

        return filtered
    def display_documents(self):
        # Supprimer uniquement les cartes actuellement affichées
        for card in self.document_cards:
            card.destroy()

        self.document_cards.clear()
        self.empty_message.grid_remove()
        self.pagination_frame.grid_remove()

        filtered_documents = self.get_filtered_documents()

        if not filtered_documents:
            self.empty_message.grid(
                row=0,
                column=0,
                pady=40,
            )
            return

        # Calculer le nombre de pages
        total_pages = (
            len(filtered_documents) + self.PAGE_SIZE - 1
        ) // self.PAGE_SIZE

        # Éviter de rester sur une page qui n'existe plus
        self.current_page = min(
            self.current_page,
            total_pages - 1,
        )

        # Sélectionner uniquement les documents de la page actuelle
        start = self.current_page * self.PAGE_SIZE
        end = start + self.PAGE_SIZE

        page_documents = filtered_documents[start:end]

        for index, document in enumerate(page_documents):
            card = DocumentCard(
                self.list_frame,
                document=document,
                on_details=lambda selected_document=document:
                    self.select_document(selected_document),
                on_print=lambda selected_document=document:
                    self.print_document(selected_document),
            )

            card.grid(
                row=index,
                column=0,
                sticky="ew",
                padx=10,
                pady=(10, 0),
            )

            self.document_cards.append(card)

        # Afficher les commandes de pagination
        if total_pages > 1:
            self.pagination_frame.grid(
                row=len(page_documents),
                column=0,
                pady=15,
            )

            self.page_label.configure(
                text=f"Page {self.current_page + 1} / {total_pages}"
            )

            self.previous_button.configure(
                state="normal" if self.current_page > 0 else "disabled"
            )

            self.next_button.configure(
                state="normal"
                if self.current_page < total_pages - 1
                else "disabled"
            )
    def previous_page(self):
                 if self.current_page > 0:
                   self.current_page -= 1
                   self.display_documents()

    def next_page(self):
        filtered_documents = self.get_filtered_documents()

        total_pages = (
            len(filtered_documents) + self.PAGE_SIZE - 1
        ) // self.PAGE_SIZE

        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.display_documents()

    def print_document(self, document):
        """Envoyer un document à l'application d'impression Windows."""

        file_path = document.get("path")

        if not file_path:
            messagebox.showwarning(
                "Impression",
                "Aucun chemin n'est associé à ce document.",
            )
            return

        path = Path(file_path)

        if not path.is_file():
            messagebox.showerror(
                "Impression",
                "Le fichier est introuvable.\n\n"
                f"Chemin : {path}",
            )
            return

        if os.name != "nt":
            messagebox.showerror(
                "Impression",
                "Cette fonctionnalité est actuellement prévue pour Windows.",
            )
            return

        try:
            os.startfile(str(path), "print")

        except OSError as error:
            messagebox.showerror(
                "Erreur d'impression",
                "Impossible de lancer l'impression.\n\n"
                "Vérifiez qu'une application compatible est installée "
                "et associée à ce format de fichier.\n\n"
                f"Détail : {error}",
            )

    def select_document(self, document):
        self.preview_panel.show_document(document)

    def change_document_status(self, document):
        """Modifier temporairement le statut dans l'interface."""

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
