
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class DocumentStatusBadge(ctk.CTkFrame):
    """Badge visuel représentant le statut de traitement d'un document."""

    STATUS_STYLES = {
        "Reçu": {
            "background": colors.SURFACE_ALT,
            "foreground": colors.TEXT_SECONDARY,
        },
        "En traitement": {
            "background": colors.PRIMARY_LIGHT,
            "foreground": colors.PRIMARY,
        },
        "À vérifier": {
            "background": colors.WARNING_LIGHT,
            "foreground": colors.WARNING,
        },
        "Classé automatiquement": {
            "background": colors.SUCCESS_LIGHT,
            "foreground": colors.SUCCESS,
        },
        "Erreur": {
            "background": colors.ERROR_LIGHT,
            "foreground": colors.ERROR,
        },
    }

    def __init__(self, parent, status="Reçu"):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=8,
        )

        self.status_label = ctk.CTkLabel(
            self,
            text="",
            height=27,
            corner_radius=7,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
                weight="bold",
            ),
        )
        self.status_label.pack()

        self.set_status(status)

    def set_status(self, status):
        """Met à jour le texte et les couleurs du badge."""

        style = self.STATUS_STYLES.get(
            status,
            {
                "background": colors.SURFACE_ALT,
                "foreground": colors.TEXT_SECONDARY,
            },
        )

        self.status_label.configure(
            text=status,
            fg_color=style["background"],
            text_color=style["foreground"],
        )
