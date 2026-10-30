

import os
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox

from frontend.ui.styles import colors, typography
from frontend.ui.components.document_status_badge import DocumentStatusBadge


class DocumentPreviewPanel(ctk.CTkScrollableFrame):
    """Panneau latéral affichant l'aperçu et les informations d'un document."""

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=colors.BORDER,
        )

        self.grid_columnconfigure(0, weight=1)
        self.current_document = None

        # En-tête
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=18)
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header,
            text="Aperçu du document",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.close_button = ctk.CTkButton(
            header,
            text="×",
            width=30,
            height=30,
            corner_radius=8,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            command=self.clear_document,
        )
        self.close_button.grid(row=0, column=1, sticky="e")

        # Zone d'aperçu
        self.preview_area = ctk.CTkFrame(
            self,
            fg_color=colors.BACKGROUND,
            corner_radius=10,
            height=170,
        )
        self.preview_area.grid(
            row=1, column=0, sticky="ew", padx=18, pady=(0, 18)
        )
        self.preview_area.grid_propagate(False)
        self.preview_area.grid_columnconfigure(0, weight=1)
        self.preview_area.grid_rowconfigure((0, 1), weight=1)

        self.preview_icon = ctk.CTkLabel(
            self.preview_area,
            text="PDF",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=colors.PRIMARY,
        )
        self.preview_icon.grid(row=0, column=0, sticky="s", pady=(20, 4))

        self.preview_message = ctk.CTkLabel(
            self.preview_area,
            text="Sélectionnez un document pour consulter son aperçu.",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
            wraplength=230,
            justify="center",
        )
        self.preview_message.grid(
            row=1, column=0, sticky="n", padx=12, pady=(4, 20)
        )

        # Informations du document
        self.info_title = ctk.CTkLabel(
            self,
            text="Informations",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SUBSECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        self.info_title.grid(
            row=2, column=0, sticky="w", padx=18, pady=(0, 12)
        )

        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(
            row=3, column=0, sticky="ew", padx=18, pady=(0, 12)
        )
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.info_labels = {}

        for index, (label, key) in enumerate([
            ("Nom du fichier", "name"),
            ("Client", "client"),
            ("Type", "type"),
            ("Date de réception", "date"),
            ("Taille", "size"),
        ]):
            row = ctk.CTkFrame(self.info_frame, fg_color="transparent")
            row.grid(row=index, column=0, sticky="ew", pady=5)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(
                    family=typography.FONT_FAMILY,
                    size=typography.CAPTION_SIZE,
                ),
                text_color=colors.TEXT_SECONDARY,
            ).grid(row=0, column=0, sticky="w")

            value_label = ctk.CTkLabel(
                row,
                text="-",
                font=ctk.CTkFont(
                    family=typography.FONT_FAMILY,
                    size=typography.CAPTION_SIZE,
                    weight="bold",
                ),
                text_color=colors.TEXT_PRIMARY,
                anchor="e",
            )
            value_label.grid(row=0, column=1, sticky="e", padx=(8, 0))

            self.info_labels[key] = value_label

        # Statut
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(
            row=4, column=0, sticky="ew", padx=18, pady=(4, 12)
        )

        ctk.CTkLabel(
            self.status_frame,
            text="Statut",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 12))

        self.status_badge = DocumentStatusBadge(
            self.status_frame,
            status="À vérifier",
        )
        self.status_badge.pack(side="left")

       

        self.clear_document()

    def show_document(self, document):
        """Affiche les informations du document sélectionné."""
        self.current_document = document

        for key, label in self.info_labels.items():
            label.configure(text=str(document.get(key, "-")))

        status = document.get("status", "À vérifier")
        self.status_badge.set_status(status)

        self.preview_icon.configure(
            text=document.get("type", "Fichier").upper()
        )
        self.preview_message.configure(
            text=(
                f"Aperçu de {document.get('name', 'ce document')}\n"
                "L'aperçu réel sera disponible prochainement."
            )
        )


    def clear_document(self):
        """Réinitialise le panneau lorsqu'aucun document n'est sélectionné."""
        self.current_document = None

        for label in self.info_labels.values():
            label.configure(text="-")

        self.status_badge.pack_forget()

        self.preview_icon.configure(text="Fichier")
        self.preview_message.configure(
            text="Sélectionnez un document dans la liste pour afficher ses informations."
        )


    def open_document(self):
        """Ouvre le document sélectionné avec le logiciel par défaut."""

        if self.current_document is None:
            messagebox.showwarning(
                "Aucun document",
                "Veuillez sélectionner un document.",
                parent=self,
            )
            return

        file_path = self.current_document.get("path")

        if not file_path:
            messagebox.showinfo(
                "Document de démonstration",
                "Le chemin du fichier sera disponible après la connexion au backend.",
                parent=self,
            )
            return

        path = Path(file_path)

        if not path.is_file():
            messagebox.showerror(
                "Fichier introuvable",
                "Le fichier demandé n'existe pas à cet emplacement.",
                parent=self,
            )
            return

        try:
            os.startfile(str(path))
        except OSError as error:
            messagebox.showerror(
                "Erreur d'ouverture",
                f"Impossible d'ouvrir le fichier : {error}",
                parent=self,
            )
