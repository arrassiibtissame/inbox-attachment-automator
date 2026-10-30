
import customtkinter as ctk

from frontend.ui.styles import colors, typography
from frontend.ui.components.document_status_badge import DocumentStatusBadge


class DocumentDetailsDialog(ctk.CTkToplevel):
    """Fenêtre affichant les détails d'un document."""

    def __init__(self, parent, document):
        super().__init__(parent)

        self.document = document

        self.title("Détails du document")
        self.geometry("520x480")
        self.resizable(False, False)
        self.configure(fg_color=colors.BACKGROUND)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=14,
        )
        container.pack(
            fill="both",
            expand=True,
            padx=24,
            pady=24,
        )

        title = ctk.CTkLabel(
            container,
            text="Informations du document",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        title.pack(anchor="w", padx=20, pady=(20, 16))

        self._add_information("Nom du fichier", "name")
        self._add_information("Client", "client")
        self._add_information("Type de fichier", "type")
        self._add_information("Date de réception", "date")
        self._add_information("Taille", "size")

        status_frame = ctk.CTkFrame(
            container,
            fg_color="transparent",
        )
        status_frame.pack(fill="x", padx=20, pady=(12, 8))

        status_title = ctk.CTkLabel(
            status_frame,
            text="Statut",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_SECONDARY,
        )
        status_title.pack(side="left", padx=(0, 12))

        DocumentStatusBadge(
            status_frame,
            status=self.document.get("status", "À vérifier"),
        ).pack(side="left")

        close_button = ctk.CTkButton(
            container,
            text="Fermer",
            height=38,
            corner_radius=8,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=self.destroy,
        )
        close_button.pack(
            fill="x",
            padx=20,
            pady=(16, 20),
        )

    def _add_information(self, label, key):
        row = ctk.CTkFrame(
            self.winfo_children()[0],
            fg_color="transparent",
        )
        row.pack(fill="x", padx=20, pady=6)

        label_widget = ctk.CTkLabel(
            row,
            text=label,
            width=150,
            anchor="w",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        )
        label_widget.pack(side="left")

        value_widget = ctk.CTkLabel(
            row,
            text=str(self.document.get(key, "-")),
            anchor="w",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BODY_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        value_widget.pack(side="left", fill="x", expand=True)
