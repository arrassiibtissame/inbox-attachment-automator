
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class PageHeader(ctk.CTkFrame):
    """En-tÃªte rÃ©utilisable pour les pages de CabinetFlow."""

    def __init__(
        self,
        parent,
        title: str,
        subtitle: str,
    ):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.PAGE_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BODY_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

