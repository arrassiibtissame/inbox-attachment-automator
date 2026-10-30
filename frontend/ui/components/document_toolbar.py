
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class DocumentToolbar(ctk.CTkFrame):
    """Barre de recherche et filtres de la page Documents."""

    def __init__(self, parent, on_search=None, on_filter=None):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.on_search = on_search
        self.on_filter = on_filter
        self.selected_filter = "Tous"

        self.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Rechercher un document ou un client...",
            height=40,
            corner_radius=9,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BODY_SIZE,
            ),
            border_color=colors.BORDER,
            fg_color=colors.SURFACE,
        )
        self.search_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 12),
        )

        self.search_entry.bind(
            "<KeyRelease>",
            self._handle_search,
        )

        self.filter_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.filter_frame.grid(
            row=0,
            column=1,
            sticky="e",
        )

        self.filter_buttons = {}

        filters = ["Tous", "À vérifier", "Classés"]

        for index, filter_name in enumerate(filters):
            button = ctk.CTkButton(
                self.filter_frame,
                text=filter_name,
                height=38,
                width=105 if filter_name == "À vérifier" else 85,
                corner_radius=8,
                font=ctk.CTkFont(
                    family=typography.FONT_FAMILY,
                    size=typography.LABEL_SIZE,
                    weight="bold",
                ),
                command=lambda name=filter_name: self.set_filter(name),
            )
            button.grid(
                row=0,
                column=index,
                padx=(0, 6 if index < 2 else 0),
            )

            self.filter_buttons[filter_name] = button

        self._update_filter_styles()

    def _handle_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_entry.get().strip())

    def set_filter(self, filter_name):
        self.selected_filter = filter_name
        self._update_filter_styles()

        if self.on_filter:
            self.on_filter(filter_name)

    def _update_filter_styles(self):
        for name, button in self.filter_buttons.items():
            is_selected = name == self.selected_filter

            button.configure(
                fg_color=(
                    colors.PRIMARY if is_selected else colors.SURFACE
                ),
                hover_color=(
                    colors.PRIMARY_HOVER
                    if is_selected
                    else colors.SURFACE_ALT
                ),
                text_color=(
                    colors.SURFACE
                    if is_selected
                    else colors.TEXT_SECONDARY
                ),
                border_width=0 if is_selected else 1,
                border_color=colors.BORDER,
            )
