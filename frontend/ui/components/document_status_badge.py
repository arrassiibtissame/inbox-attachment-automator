
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class DocumentStatusBadge(ctk.CTkFrame):
    """Badge visuel indiquant le statut d'un document."""

    STATUS_STYLES = {
        "À vérifier": {
            "background": colors.WARNING_LIGHT,
            "foreground": colors.WARNING,
        },
        "Classé": {
            "background": colors.SUCCESS_LIGHT,
            "foreground": colors.SUCCESS,
        },
    }

    def __init__(self, parent, status="À vérifier"):
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
                size=11,
                weight="bold",
            ),
        )
        self.status_label.pack()

        self.set_status(status)

    def set_status(self, status):
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
