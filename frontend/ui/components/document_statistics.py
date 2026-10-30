
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class DocumentStatistics(ctk.CTkFrame):
    """Affiche les statistiques principales des documents."""

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="transparent",
            corner_radius=0,
        )

        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.total_value = self._create_stat_card(
            column=0,
            title="Total des documents",
            value="0",
            value_color=colors.TEXT_PRIMARY,
        )

        self.pending_value = self._create_stat_card(
            column=1,
            title="À vérifier",
            value="0",
            value_color=colors.WARNING,
        )

        self.classified_value = self._create_stat_card(
            column=2,
            title="Classés",
            value="0",
            value_color=colors.SUCCESS,
        )

    def _create_stat_card(self, column, title, value, value_color):
        card = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=colors.BORDER,
        )
        card.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 7, 7 if column < 2 else 0),
        )

        card.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.LABEL_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        )
        title_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=16,
            pady=(15, 5),
        )

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.STAT_VALUE_SIZE,
                weight="bold",
            ),
            text_color=value_color,
        )
        value_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=16,
            pady=(0, 15),
        )

        return value_label

    def update_statistics(self, total, pending, classified):
        self.total_value.configure(text=str(total))
        self.pending_value.configure(text=str(pending))
        self.classified_value.configure(text=str(classified))
