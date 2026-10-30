
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientInfoSection(ctk.CTkFrame):
    """Displays the main contact information of a client."""

    def __init__(
        self,
        parent,
        contact="Contact non renseigné",
        phone="",
        tax_id="",
        email="",
    ):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(1, weight=1)

        information = [
            ("Contact", contact),
            ("Téléphone", phone or "Non renseigné"),
            ("Identifiant fiscal", tax_id or "Non renseigné"),
            ("Email", email or "Non renseigné"),
        ]

        for row, (label, value) in enumerate(information):
            ctk.CTkLabel(
                self,
                text=label,
                font=ctk.CTkFont(
                    family=typography.FONT_FAMILY,
                    size=11,
                ),
                text_color=colors.TEXT_MUTED,
                anchor="w",
            ).grid(
                row=row,
                column=0,
                sticky="w",
                pady=4,
                padx=(0, 12),
            )

            ctk.CTkLabel(
                self,
                text=value,
                font=ctk.CTkFont(
                    family=typography.FONT_FAMILY,
                    size=12,
                ),
                text_color=colors.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=280,
            ).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=4,
            )
