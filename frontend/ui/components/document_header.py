
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class DocumentHeader(ctk.CTkFrame):
    """En-tête de la page Documents."""

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(
            self,
            text="Documents",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.PAGE_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        self.title.grid(row=0, column=0, sticky="w")

        self.description = ctk.CTkLabel(
            self,
            text="Consultez, vérifiez et organisez les documents de vos clients.",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BODY_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        )
        self.description.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(5, 0),
        )
