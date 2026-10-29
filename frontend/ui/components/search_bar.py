
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class SearchBar(ctk.CTkFrame):
    """Barre de recherche réutilisable avec bouton de filtre."""

    def __init__(
        self,
        parent,
        placeholder="Rechercher...",
        on_search=None,
        on_filter=None,
    ):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=colors.BORDER,
        )

        self.on_search = on_search
        self.on_filter = on_filter

        self.grid_columnconfigure(0, weight=1)

        self.search_input = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            height=44,
            corner_radius=9,
            border_width=1,
            border_color=colors.BORDER,
            fg_color=colors.BACKGROUND,
            text_color=colors.TEXT_PRIMARY,
            placeholder_text_color=colors.TEXT_MUTED,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BODY_SIZE,
            ),
        )
        self.search_input.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(14, 10),
            pady=14,
        )

        self.search_input.bind(
            "<KeyRelease>",
            self._handle_search,
        )

        self.filter_button = ctk.CTkButton(
            self,
            text="☷  Filtrer",
            width=108,
            height=44,
            corner_radius=9,
            border_width=1,
            border_color=colors.BORDER,
            fg_color=colors.SURFACE,
            hover_color=colors.SURFACE_ALT,
            text_color=colors.TEXT_SECONDARY,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
                weight="bold",
            ),
            command=self._handle_filter,
        )
        self.filter_button.grid(
            row=0,
            column=1,
            padx=(0, 14),
            pady=14,
        )

    def _handle_search(self, event=None):
        if self.on_search:
            self.on_search(self.search_input.get().strip())

    def _handle_filter(self):
        if self.on_filter:
            self.on_filter()

    def get_search_text(self):
        return self.search_input.get().strip()
