
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class StatCard(ctk.CTkFrame):
    """Carte réutilisable pour afficher une statistique."""

    def __init__(
        self,
        parent,
        title: str,
        value: str,
        subtitle: str,
        accent_color: str,
    ):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 8))

        ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.STAT_VALUE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=1, column=0, sticky="w", padx=18)

        ctk.CTkLabel(
            self,
            text=subtitle,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=2, column=0, sticky="w", padx=18, pady=(4, 18))

        ctk.CTkFrame(
            self,
            height=4,
            fg_color=accent_color,
            corner_radius=2,
        ).grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 14))

