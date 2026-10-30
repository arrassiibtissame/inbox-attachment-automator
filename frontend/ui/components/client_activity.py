import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientActivity(ctk.CTkFrame):
    """Displays the last activity date of a client."""

    def __init__(self, parent, last_activity="Aucune activité"):
        super().__init__(parent, fg_color="transparent")

        self.activity_label = ctk.CTkLabel(
            self,
            text=f"Dernière activité : {last_activity}",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=11,
            ),
            text_color=colors.TEXT_MUTED,
            anchor="w",
        )
        self.activity_label.pack(anchor="w")