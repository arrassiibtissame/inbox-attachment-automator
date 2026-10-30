import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientCardActions(ctk.CTkFrame):
    """Contains the action buttons of a client card."""

    def __init__(
        self,
        parent,
        on_open=None,
        on_edit=None,
        on_delete=None,
    ):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure((0, 1, 2), weight=1)

        button_style = {
            "height": 34,
            "corner_radius": 8,
            "font": ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=12,
                weight="bold",
            ),
        }

        ctk.CTkButton(
            self,
            text="Ouvrir",
            command=on_open,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            **button_style,
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(
            self,
            text="Modifier",
            command=on_edit,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            **button_style,
        ).grid(row=0, column=1, padx=5, sticky="ew")

        ctk.CTkButton(
            self,
            text="Supprimer",
            command=on_delete,
            fg_color=colors.ERROR_LIGHT,
            hover_color=colors.ERROR,
            text_color=colors.ERROR,
            **button_style,
        ).grid(row=0, column=2, padx=(5, 0), sticky="ew")
