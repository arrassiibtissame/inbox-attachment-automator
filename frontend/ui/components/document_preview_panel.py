
import os
from pathlib import Path

import customtkinter as ctk
import pymupdf

from PIL import Image

from tkinter import messagebox

from frontend.ui.styles import colors, typography
from frontend.ui.components.document_status_badge import DocumentStatusBadge


class DocumentPreviewPanel(ctk.CTkScrollableFrame):
    """Panneau latéral avec aperçu réel des documents."""

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
        self.pdf_document = None
        self.current_page = 0
        self.zoom = 1.0
        self.preview_image = None
        self.pil_image = None

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
        )
        self.preview_area.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 10),
        )
        self.preview_area.grid_columnconfigure(0, weight=1)

        self.preview_icon = ctk.CTkLabel(
            self.preview_area,
            text="Fichier",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=colors.PRIMARY,
        )
        self.preview_icon.grid(
            row=0,
            column=0,
            pady=(25, 5),
        )

        self.preview_message = ctk.CTkLabel(
            self.preview_area,
            text="Sélectionnez un document pour consulter son aperçu.",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
            wraplength=400,
            justify="center",
        )
        self.preview_message.grid(
            row=1,
            column=0,
            padx=12,
            pady=(5, 25),
        )

        # Image réelle du document
        self.image_label = ctk.CTkLabel(
            self.preview_area,
            text="",
        )
        self.image_label.grid(
            row=2,
            column=0,
            padx=8,
            pady=8,
        )

        # Commandes PDF
        self.pdf_controls = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.pdf_controls.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 18),
        )
        self.pdf_controls.grid_columnconfigure(1, weight=1)

        self.previous_button = ctk.CTkButton(
            self.pdf_controls,
            text="‹",
            width=35,
            height=30,
            command=self.previous_page,
        )
        self.previous_button.grid(row=0, column=0, padx=3)

        self.page_label = ctk.CTkLabel(
            self.pdf_controls,
            text="Page 0 / 0",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        self.page_label.grid(row=0, column=1, padx=5)

        self.next_button = ctk.CTkButton(
            self.pdf_controls,
            text="›",
            width=35,
            height=30,
            command=self.next_page,
        )
        self.next_button.grid(row=0, column=2, padx=3)

        self.zoom_out_button = ctk.CTkButton(
            self.pdf_controls,
            text="−",
            width=35,
            height=30,
            command=self.zoom_out,
        )
        self.zoom_out_button.grid(row=1, column=0, padx=3, pady=(8, 0))

        self.zoom_label = ctk.CTkLabel(
            self.pdf_controls,
            text="100 %",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        self.zoom_label.grid(row=1, column=1, pady=(8, 0))

        self.zoom_in_button = ctk.CTkButton(
            self.pdf_controls,
            text="+",
            width=35,
            height=30,
            command=self.zoom_in,
        )
        self.zoom_in_button.grid(row=1, column=2, padx=3, pady=(8, 0))

        self.open_button = ctk.CTkButton(
            self,
            text="Ouvrir avec Windows",
            height=34,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            text_color=colors.SURFACE,
            command=self.open_document,
        )
        self.open_button.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 18),
        )

        # Informations
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
            row=4,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 12),
        )

        self.info_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.info_frame.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 12),
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
            row = ctk.CTkFrame(
                self.info_frame,
                fg_color="transparent",
            )
            row.grid(
                row=index,
                column=0,
                sticky="ew",
                pady=5,
            )
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
            value_label.grid(
                row=0,
                column=1,
                sticky="e",
                padx=(8, 0),
            )

            self.info_labels[key] = value_label

        # Statut
        self.status_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.status_frame.grid(
            row=6,
            column=0,
            sticky="ew",
            padx=18,
            pady=(4, 18),
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

    def _clear_preview_image(self):
        """Détruire le label avant de libérer l'image Tk qu'il affichait.

        Avec certaines versions de CustomTkinter, configure(image=None)
        ne retire pas réellement l'ancienne image interne du label. Le widget
        peut alors conserver une référence vers un identifiant Tk supprimé.
        Détruire puis recréer le label évite cette situation.
        """
        if hasattr(self, "image_label") and self.image_label is not None:
            try:
                self.image_label.destroy()
            except Exception:
                pass

        # Le label n'utilise désormais plus l'image : on peut libérer les références.
        self.preview_image = None
        self.pil_image = None

        self.image_label = ctk.CTkLabel(
            self.preview_area,
            text="",
        )
        self.image_label.grid(
            row=2,
            column=0,
            padx=8,
            pady=8,
        )

    def show_document(self, document):
        """Afficher un document et ses informations."""

        self._close_pdf()
        self._clear_preview_image()

        self.current_document = document
        self.current_page = 0
        self.zoom = 1.0

        for key, label in self.info_labels.items():
            label.configure(text=str(document.get(key, "-")))

        self.status_badge.pack(side="left")
        self.status_badge.set_status(
            document.get("status", "À vérifier")
        )

        self.preview_icon.grid()
        self.preview_message.grid()

        extension = Path(
            document.get("path", document.get("name", ""))
        ).suffix.lower()

        file_path = document.get("path")

        if not file_path or not Path(file_path).is_file():
            self._show_error("Le fichier est introuvable.")
            return

        try:
            if extension == ".pdf":
                self._load_pdf(file_path)

            elif extension in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                self._load_image(file_path)

            else:
                self._show_unsupported(extension)

        except Exception as error:
            print(f"Erreur de prévisualisation : {error}")
            self._show_error(
                "Impossible de prévisualiser ce document."
            )

    def _load_pdf(self, file_path):
        """Charger un document PDF."""

        self.pdf_document = pymupdf.open(file_path)

        if len(self.pdf_document) == 0:
            self._show_error("Ce PDF ne contient aucune page.")
            return

        self.preview_icon.grid_remove()
        self.preview_message.grid_remove()

        self.pdf_controls.grid()
        self.render_pdf_page()

    def render_pdf_page(self):
        """Afficher la page PDF actuelle."""

        if self.pdf_document is None:
            return

        page = self.pdf_document.load_page(self.current_page)

        matrix = pymupdf.Matrix(self.zoom, self.zoom)
        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        image = Image.frombytes(
            "RGB",
            [pixmap.width, pixmap.height],
            pixmap.samples,
        )

        max_width = 560
        max_height = 750

        image.thumbnail(
            (int(max_width * self.zoom), int(max_height * self.zoom)),
            Image.Resampling.LANCZOS,
        )

        self._clear_preview_image()
        self.preview_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=image.size,
        )

        self.image_label.configure(
            image=self.preview_image,
            text="",
        )

        self.page_label.configure(
            text=f"Page {self.current_page + 1} / {len(self.pdf_document)}"
        )

        self.zoom_label.configure(
            text=f"{int(self.zoom * 100)} %"
        )

        self.previous_button.configure(
            state="normal" if self.current_page > 0 else "disabled"
        )

        self.next_button.configure(
            state=(
                "normal"
                if self.current_page < len(self.pdf_document) - 1
                else "disabled"
            )
        )

    def _load_image(self, file_path):
        """Afficher une image."""

        self.preview_icon.grid_remove()
        self.preview_message.grid_remove()
        self.pdf_controls.grid_remove()

        with Image.open(file_path) as source:
            image = source.convert("RGB")

        image.thumbnail((520, 650), Image.Resampling.LANCZOS)

        self._clear_preview_image()
        self.pil_image = image

        self.preview_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=image.size,
        )

        self.image_label.configure(
            image=self.preview_image,
            text="",
        )

    def _show_unsupported(self, extension):
        """Gérer les formats non pris en charge pour l'aperçu."""

        self.pdf_controls.grid_remove()

        self.preview_icon.configure(
            text=extension.upper().replace(".", "") or "Fichier"
        )

        self.preview_message.configure(
            text="L'aperçu intégré de ce format n'est pas encore disponible."
        )

    def _show_error(self, message):
        """Afficher un message d'erreur."""

        self.pdf_controls.grid_remove()
        self._clear_preview_image()

        self.preview_icon.configure(text="Erreur")
        self.preview_message.configure(text=message)

    def previous_page(self):
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.render_pdf_page()

    def next_page(self):
        if (
            self.pdf_document
            and self.current_page < len(self.pdf_document) - 1
        ):
            self.current_page += 1
            self.render_pdf_page()

    def zoom_in(self):
        if self.pdf_document and self.zoom < 2.0:
            self.zoom = min(2.0, self.zoom + 0.2)
            self.render_pdf_page()

    def zoom_out(self):
        if self.pdf_document and self.zoom > 0.6:
            self.zoom = max(0.6, self.zoom - 0.2)
            self.render_pdf_page()

    def _close_pdf(self):
        """Fermer le PDF sans libérer prématurément l'image affichée."""
        if self.pdf_document is not None:
            self.pdf_document.close()
            self.pdf_document = None

    def clear_document(self):
        """Réinitialiser le panneau."""

        self._close_pdf()
        self._clear_preview_image()

        self.current_document = None

        for label in self.info_labels.values():
            label.configure(text="-")

        self.status_badge.pack_forget()

        self.preview_icon.configure(text="Fichier")
        self.preview_icon.grid()

        self.preview_message.configure(
            text="Sélectionnez un document dans la liste pour afficher son aperçu."
        )
        self.preview_message.grid()

        self.pdf_controls.grid_remove()

    def open_document(self):
        """Ouvrir le fichier avec le logiciel Windows par défaut."""

        if self.current_document is None:
            messagebox.showwarning(
                "Aucun document",
                "Veuillez sélectionner un document.",
                parent=self,
            )
            return

        file_path = self.current_document.get("path")

        if not file_path:
            messagebox.showwarning(
                "Chemin indisponible",
                "Le chemin du fichier est introuvable.",
                parent=self,
            )
            return

        path = Path(file_path)

        if not path.is_file():
            messagebox.showerror(
                "Fichier introuvable",
                "Le fichier demandé n'existe pas.",
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
