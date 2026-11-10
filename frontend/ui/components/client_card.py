
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientCard(ctk.CTkFrame):
    """Client card displaying the company name and responsible employee."""

    def __init__(
        self,
        parent,
        name,
        contact="Contact non renseigné",
        phone="",
        tax_id="",
        email="Email non renseigné",
        responsible_name="Non attribué",
        document_count=0,
        last_activity="Aucune activité",
        on_open=None,
        on_edit=None,
        on_delete=None,
    ):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=colors.BORDER,
            height=100,
        )

        self.on_open = on_open

        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

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
        )
        self.name_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(16, 2),
        )

        self.responsible_label = ctk.CTkLabel(
            self,
            text=f"Responsable : {responsible_name}",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=12,
            ),
            text_color=colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.responsible_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 14),
        )

        self.bind("<Button-1>", self._handle_open)
        self.name_label.bind("<Button-1>", self._handle_open)
        self.responsible_label.bind("<Button-1>", self._handle_open)

    def _handle_open(self, event=None):
        if self.on_open:
            self.on_open()
