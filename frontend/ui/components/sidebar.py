
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from frontend.ui.styles import colors, typography


LOGO_PATH = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "fidomek_one_logo.png"
)


class Sidebar(ctk.CTkFrame):
    """Barre latérale de navigation de FIDOMEK ONE."""

    def __init__(self, parent, on_navigate):
        super().__init__(
            parent,
            width=235,
            corner_radius=0,
            fg_color=colors.SURFACE,
            border_width=1,
            border_color=colors.BORDER,
        )

        self.on_navigate = on_navigate
        self.nav_buttons = {}

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Identité de la société
        brand_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        brand_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=14,
            pady=(20, 16),
        )
        brand_frame.grid_columnconfigure(0, weight=1)

        if LOGO_PATH.exists():
            try:
                with Image.open(LOGO_PATH) as image:
                    logo_pil = image.convert("RGBA")

                self.logo_image = ctk.CTkImage(
                    light_image=logo_pil,
                    dark_image=logo_pil,
                    size=(195, 98),
                )

                ctk.CTkLabel(
                    brand_frame,
                    text="",
                    image=self.logo_image,
                    fg_color="transparent",
                ).grid(
                    row=0,
                    column=0,
                    sticky="ew",
                    padx=0,
                    pady=0,
                )
            except Exception as error:
                print(f"Erreur de chargement du logo : {error}")
        else:
            print(f"Logo introuvable : {LOGO_PATH}")

      

        # Titre du menu
        ctk.CTkLabel(
            self,
            text="GESTION DOCUMENTAIRE",
            font=(typography.FONT_FAMILY, 10, "bold"),
            text_color=colors.TEXT_SECONDARY,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=18,
            pady=(10, 16),
        )

        # Navigation
        menu_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        menu_frame.grid(
            row=2,
            column=0,
            sticky="new",
            padx=12,
        )

        menu_items = [
            ("Tableau de bord", "dashboard"),
            ("Documents", "documents"),
            ("Clients", "clients"),
            ("Paramètres", "settings"),
        ]

        for label, page_name in menu_items:
            button = ctk.CTkButton(
                menu_frame,
                text=label,
                anchor="w",
                height=42,
                corner_radius=10,
                fg_color="transparent",
                hover_color=colors.PRIMARY_LIGHT,
                text_color=colors.TEXT_SECONDARY,
                font=(
                    typography.FONT_FAMILY,
                    typography.BODY_SIZE,
                ),
                command=lambda page=page_name: self.on_navigate(page),
            )
            button.pack(fill="x", pady=4)
            self.nav_buttons[page_name] = button

        # Pied de page
        ctk.CTkLabel(
            self,
            text="FIDOMEK ONE · v1.0.0",
            font=(
                typography.FONT_FAMILY,
                typography.CAPTION_SIZE,
            ),
            text_color=colors.TEXT_SECONDARY,
        ).grid(
            row=3,
            column=0,
            sticky="w",
            padx=18,
            pady=20,
        )

    def set_active(self, active_page):
        """Met en évidence la page sélectionnée."""

        for page_name, button in self.nav_buttons.items():
            selected = page_name == active_page

            button.configure(
                fg_color=(
                    colors.PRIMARY_LIGHT
                    if selected
                    else "transparent"
                ),
                text_color=(
                    colors.PRIMARY
                    if selected
                    else colors.TEXT_SECONDARY
                ),
                font=(
                    typography.FONT_FAMILY,
                    typography.BODY_SIZE,
                    "bold" if selected else "normal",
                ),
            )

