
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientCardHeader(ctk.CTkFrame):
    """En-tête d'une carte client : avatar, nom et nombre de documents."""

    def __init__(self, parent, name, document_count=0):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(1, weight=1)

        initials = name.strip()[:1].upper() if name.strip() else "?"

        self.avatar = ctk.CTkLabel(
            self,
            text=initials,
            width=44,
            height=44,
            corner_radius=12,
            fg_color=colors.PRIMARY_LIGHT,
            text_color=colors.PRIMARY,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=18,
                weight="bold",
            ),
        )
        self.avatar.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(0, 12),
            sticky="ns",
        )

        self.name_label = ctk.CTkLabel(
            self,
            text=name,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=15,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=280,
        )
        self.name_label.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=(2, 4),
        )

        self.documents_label = ctk.CTkLabel(
            self,
            text=f"{document_count} document(s)",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=11,
            ),
            text_color=colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.documents_label.grid(
            row=1,
            column=1,
            sticky="w",
        )
