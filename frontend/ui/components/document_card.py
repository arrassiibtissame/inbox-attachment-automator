
import customtkinter as ctk

from frontend.ui.styles import colors, typography
from frontend.ui.components.document_status_badge import DocumentStatusBadge


class DocumentCard(ctk.CTkFrame):
    """Carte présentant un document sélectionnable."""

    def __init__(
        self,
        parent,
        document,
        on_details=None,
        on_print=None,
    ):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=colors.BORDER,
        )

        self.document = document
        self.on_details = on_details
        self.on_print = on_print

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
            f"{document.get('client', 'Non attribué')}  •  "
            f"{document.get('type', 'Inconnu')}  •  "
            f"{document.get('date', '-')}"
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

        # Statut du document
        self.status_badge = DocumentStatusBadge(
            self,
            status=document.get("status", "Reçu"),
        )
        self.status_badge.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=10,
            pady=12,
        )

        # Bouton de consultation
        self.details_button = ctk.CTkButton(
            self,
            text="Afficher",
            width=85,
            height=32,
            corner_radius=8,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            text_color=colors.SURFACE,
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
            padx=(0, 8),
        )

        # Bouton d'impression
        self.print_button = ctk.CTkButton(
            self,
            text="Imprimer",
            width=85,
            height=32,
            corner_radius=8,
            fg_color=colors.SURFACE,
            hover_color=colors.BORDER,
            border_width=1,
            border_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
            ),
            command=self._print_document,
        )
        self.print_button.grid(
            row=0,
            column=3,
            rowspan=2,
            padx=(0, 16),
        )

    def _show_details(self):
        if self.on_details:
            self.on_details(self.document)

    def _print_document(self):
        if self.on_print:
            self.on_print(self.document)
