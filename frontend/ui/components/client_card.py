import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientCard(ctk.CTkFrame):

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
        is_archived=False,
        on_restore=None,
    ):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=colors.BORDER,
            height=142,
        )

        self.on_open = on_open
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.is_archived = is_archived
        self.on_restore = on_restore

        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        self.name_label = ctk.CTkLabel(
            self,
            text=name,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=16,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
            anchor="w",
        )
        self.name_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=16,
            pady=(13, 3),
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
            padx=16,
            pady=(0, 9),
        )

        actions = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        actions.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=12,
            pady=(0, 12),
        )
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            actions,
            text="Ouvrir",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=self._handle_open,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=3,
        )

        self.edit_button = ctk.CTkButton(
            actions,
            text="Archiv?" if self.is_archived else "Modifier",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_SECONDARY if self.is_archived else colors.TEXT_PRIMARY,
            state="disabled" if self.is_archived else "normal",
            command=self._handle_edit,
        )
        self.edit_button.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=3,
        )

        self.action_button = ctk.CTkButton(
            actions,
            text="R?activer" if self.is_archived else "Archiver",
            height=30,
            corner_radius=8,
            font=ctk.CTkFont(size=11),
            fg_color=colors.PRIMARY if self.is_archived else colors.ERROR,
            hover_color=colors.PRIMARY_HOVER if self.is_archived else "#B8323B",
            command=self._handle_restore if self.is_archived else self._handle_delete,
        )
        self.action_button.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=3,
        )

        self.bind("<Button-1>", self._handle_card_click)
        self.name_label.bind("<Button-1>", self._handle_card_click)
        self.responsible_label.bind("<Button-1>", self._handle_card_click)

    def _handle_card_click(self, event=None):
        self._handle_open()

    def _handle_open(self):
        if self.on_open:
            self.on_open()

    def _handle_edit(self):
        if self.on_edit:
            self.on_edit()

    def _handle_delete(self):
        if self.on_delete:
            self.on_delete()

    def _handle_restore(self):
        if self.on_restore:
            self.on_restore()
