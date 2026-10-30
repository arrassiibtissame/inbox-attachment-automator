
import customtkinter as ctk

from frontend.ui.styles import colors, typography
from frontend.ui.components.document_status_badge import DocumentStatusBadge


class DocumentCard(ctk.CTkFrame):
    """Carte présentant les informations d'un document."""

    def __init__(self, parent, document, on_details=None):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=colors.BORDER,
        )

        self.document = document
        self.on_details = on_details

        self.grid_columnconfigure(0, weight=1)

        # Nom du document
        self.name_label = ctk.CTkLabel(
            self,
            text=document.get("name", "Document sans nom"),
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BODY_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.name_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=16,
            pady=(14, 4),
        )

        # Informations du document
        information = (
            f"Client : {document.get('client', 'Non attribué')}   •   "
            f"Type : {document.get('type', 'Inconnu')}   •   "
            f"Date : {document.get('date', '-')}   •   "
            f"Taille : {document.get('size', '-')}"
        )

        self.info_label = ctk.CTkLabel(
            self,
            text=information,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.info_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=16,
            pady=(0, 14),
        )

        # Statut et bouton de détails
        self.status_badge = DocumentStatusBadge(
            self,
            status=document.get("status", "À vérifier"),
        )
        self.status_badge.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=12,
            pady=12,
        )

        self.details_button = ctk.CTkButton(
            self,
            text="Détails",
            width=80,
            height=32,
            corner_radius=8,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
            ),
            command=self._show_details,
        )
        self.details_button.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=(0, 16),
        )

    def _show_details(self):
        if self.on_details:
            self.on_details(self.document)
