
import customtkinter as ctk

from frontend.ui.components.page_header import PageHeader
from frontend.ui.components.stat_card import StatCard
from frontend.ui.styles import colors, typography


class DashboardPage(ctk.CTkFrame):
    """Page principale de suivi de FIDOMEK ONE."""

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=colors.BACKGROUND,
            corner_radius=0,
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # En-tÃªte de la page
        header = PageHeader(
            self,
            title="Tableau de bord",
            subtitle="Vue gÃ©nÃ©rale de l'activitÃ© du cabinet",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=30,
            pady=(25, 20),
        )

        # Cartes de statistiques
        stats_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        stats_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 25),
        )

        for column in range(3):
            stats_frame.grid_columnconfigure(column, weight=1)

        StatCard(
            stats_frame,
            title="Documents reÃ§us",
            value="0",
            subtitle="Documents importÃ©s",
            accent_color=colors.PRIMARY,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10),
        )

        StatCard(
            stats_frame,
            title="Clients",
            value="0",
            subtitle="Clients enregistrÃ©s",
            accent_color=colors.ACCENT_PURPLE,
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=10,
        )

        StatCard(
            stats_frame,
            title="Ã€ vÃ©rifier",
            value="0",
            subtitle="Documents Ã  contrÃ´ler",
            accent_color=colors.WARNING,
        ).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(10, 0),
        )

        # Ã‰tat de l'automatisation e-mail
        automation_frame = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        automation_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 20),
        )
        automation_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            automation_frame,
            text="Automatisation des e-mails",
            font=(
                typography.FONT_FAMILY,
                typography.SECTION_TITLE_SIZE,
                "bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(18, 6),
        )

        ctk.CTkLabel(
            automation_frame,
            text="Connexion Gmail : Ã  relier Ã  l'interface",
            font=(typography.FONT_FAMILY, typography.BODY_SIZE),
            text_color=colors.TEXT_SECONDARY,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 5),
        )

        ctk.CTkLabel(
            automation_frame,
            text="TÃ©lÃ©chargement automatique : Ã  relier au script existant",
            font=(typography.FONT_FAMILY, typography.BODY_SIZE),
            text_color=colors.TEXT_SECONDARY,
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 18),
        )

        # Zone des documents rÃ©cents
        recent_frame = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        recent_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=30,
            pady=(0, 30),
        )
        recent_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            recent_frame,
            text="Documents rÃ©cents",
            font=(
                typography.FONT_FAMILY,
                typography.SECTION_TITLE_SIZE,
                "bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(22, 8),
        )

        ctk.CTkLabel(
            recent_frame,
            text=(
                "Aucun document pour le moment.\n"
                "Les documents apparaÃ®tront ici aprÃ¨s leur intÃ©gration."
            ),
            font=(
                typography.FONT_FAMILY,
                typography.BODY_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
            justify="center",
        ).grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=24,
            pady=35,
        )

