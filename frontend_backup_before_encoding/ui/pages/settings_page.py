
import customtkinter as ctk

from frontend.ui.components.page_header import PageHeader
from frontend.ui.styles import colors, typography


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        header = PageHeader(
            self,
            title="ParamÃ¨tres",
            subtitle="Configurez les prÃ©fÃ©rences de FIDOMEK ONE",
        )
        header.grid(
            row=0, column=0, sticky="ew",
            padx=32, pady=(30, 24)
        )

        # Apparence
        appearance_card = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        appearance_card.grid(
            row=1, column=0, sticky="ew",
            padx=32, pady=(0, 18)
        )
        appearance_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            appearance_card,
            text="Apparence",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 5))

        ctk.CTkLabel(
            appearance_card,
            text="Choisissez le thÃ¨me visuel de l'application.",
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 12))

        self.theme_option = ctk.CTkOptionMenu(
            appearance_card,
            values=["Clair", "Sombre", "SystÃ¨me"],
            command=self.change_theme,
            fg_color=colors.PRIMARY,
            button_color=colors.PRIMARY,
            button_hover_color=colors.PRIMARY_HOVER,
        )
        self.theme_option.set("Clair")
        self.theme_option.grid(
            row=2, column=0, sticky="w",
            padx=22, pady=(0, 20)
        )

        # Stockage
        storage_card = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        storage_card.grid(
            row=2, column=0, sticky="ew",
            padx=32, pady=(0, 18)
        )
        storage_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            storage_card,
            text="Stockage des documents",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 5))

        ctk.CTkLabel(
            storage_card,
            text=(
                "Le dossier de stockage sera configurable "
                "lors de l'intÃ©gration des documents."
            ),
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
            wraplength=650,
            justify="left",
        ).grid(
            row=1, column=0, sticky="w",
            padx=22, pady=(0, 20)
        )

        
        # IntÃ©gration Gmail
        gmail_card = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        gmail_card.grid(
            row=3, column=0, sticky="ew",
            padx=32, pady=(0, 18)
        )
        gmail_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            gmail_card,
            text="Connexion Ã  la messagerie",
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.SECTION_TITLE_SIZE,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(
            row=0, column=0, sticky="w",
            padx=22, pady=(20, 5)
        )

        ctk.CTkLabel(
            gmail_card,
            text=(
                "Connectez la boÃ®te Gmail autorisÃ©e du cabinet "
                "pour prÃ©parer la rÃ©cupÃ©ration automatique des piÃ¨ces jointes."
            ),
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
            wraplength=650,
            justify="left",
        ).grid(
            row=1, column=0, sticky="w",
            padx=22, pady=(0, 12)
        )

        # Ã‰tat indicatif : aucune connexion n'est encore reliÃ©e Ã  l'interface.
        status_frame = ctk.CTkFrame(
            gmail_card,
            fg_color="transparent",
        )
        status_frame.grid(
            row=2, column=0, sticky="ew",
            padx=22, pady=(0, 20)
        )

        ctk.CTkLabel(
            status_frame,
            text="Ã‰tat : non connectÃ© Ã  l'interface",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors.TEXT_SECONDARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            status_frame,
            text="TÃ©lÃ©chargement automatique : non reliÃ© Ã  l'interface",
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(6, 0))


    @staticmethod
    def change_theme(choice):
        themes = {
            "Clair": "light",
            "Sombre": "dark",
            "SystÃ¨me": "system",
        }
        ctk.set_appearance_mode(themes[choice])

