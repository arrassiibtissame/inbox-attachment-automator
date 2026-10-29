
from pathlib import Path
import customtkinter as ctk
from PIL import Image


BASE = Path(__file__).resolve().parents[2]
ASSETS_DIR = BASE / "assets"
ICONS_DIR = Path(__file__).resolve().parent / "icons"
LOGO_PATH = ASSETS_DIR / "logo3.png"

NAVY = "#122943"
NAVY_DEEP = "#0B2038"
HOVER = "#1B3853"
ACTIVE = "#10445A"
TEAL = "#0DB5AA"
WHITE = "#FFFFFF"
MUTED = "#9EB0C2"
FONT = "DM Sans"


def load_icon(name, size=(20, 20)):
    path = ICONS_DIR / f"{name}.png"

    if not path.exists():
        return None

    try:
        image = Image.open(path).convert("RGBA")
        return ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=size,
        )
    except (OSError, ValueError):
        return None


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate):
        super().__init__(
            master,
            width=256,
            fg_color=NAVY,
            corner_radius=0,
            border_width=0,
        )

        self.on_navigate = on_navigate
        self.buttons = {}
        self.icon_images = []

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_brand()
        self._build_workspace()
        self._build_navigation()
        self._build_bottom()

    
    def _build_brand(self):
        brand = ctk.CTkFrame(
            self,
            fg_color="transparent",
            height=125,
        )
        brand.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=16,
            pady=(12, 0),
        )
        brand.grid_propagate(False)
        brand.grid_columnconfigure(0, weight=1)

        # Logo centré en haut
        try:
            with Image.open(LOGO_PATH) as image:
                source = image.convert("RGBA")
            self.logo_image = ctk.CTkImage(
                light_image=source,
                dark_image=source,
                size=(46, 46),
            )
        except (OSError, ValueError):
            self.logo_image = None

        if self.logo_image is not None:
            logo = ctk.CTkLabel(
                brand,
                text="",
                image=self.logo_image,
                fg_color="transparent",
            )
        else:
            logo = ctk.CTkLabel(
                brand,
                text="F",
                width=46,
                height=46,
                font=(FONT, 28, "bold"),
                text_color=WHITE,
                fg_color="transparent",
            )

        logo.grid(row=0, column=0, pady=(0, 5))

        # Nom sous le logo
        name = ctk.CTkFrame(
            brand,
            fg_color="transparent",
        )
        name.grid(row=1, column=0)

        ctk.CTkLabel(
            name,
            text="FIDOMEK",
            font=(FONT, 16, "bold"),
            text_color=WHITE,
        ).pack(side="left")

        ctk.CTkLabel(
            name,
            text=" ONE",
            font=(FONT, 16, "bold"),
            text_color="#20C8BD",
        ).pack(side="left")


    def _fallback_logo(self, parent):
        ctk.CTkLabel(
            parent,
            text="F",
            width=40,
            height=40,
            font=(FONT, 24, "bold"),
            text_color="#20C8BD",
            fg_color="transparent",
        ).grid(row=0, column=0, padx=(4, 11))

    def _build_workspace(self):
        card = ctk.CTkFrame(
            self,
            fg_color="#203B55",
            border_width=1,
            border_color="#314C66",
            corner_radius=12,
        )
        card.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 0),
        )
        card.grid_columnconfigure(1, weight=1)

        avatar = ctk.CTkFrame(
            card,
            width=40,
            height=40,
            corner_radius=9,
            fg_color="#145064",
        )
        avatar.grid(row=0, column=0, padx=(10, 10), pady=12)
        avatar.grid_propagate(False)

        ctk.CTkLabel(
            avatar,
            text="FO",
            font=(FONT, 11, "bold"),
            text_color="#A7FFF3",
        ).place(relx=0.5, rely=0.5, anchor="center")

        copy = ctk.CTkFrame(card, fg_color="transparent")
        copy.grid(row=0, column=1, sticky="ew", pady=10)

        ctk.CTkLabel(
            copy,
            text="ESPACE DE TRAVAIL",
            font=(FONT, 8, "bold"),
            text_color="#8FA6BF",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            copy,
            text="Fidomek One",
            font=(FONT, 13, "bold"),
            text_color=WHITE,
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkLabel(
            card,
            text="›",
            font=(FONT, 23),
            text_color="#819AB4",
        ).grid(row=0, column=2, padx=(4, 12))

    def _build_navigation(self):
        ctk.CTkLabel(
            self,
            text="MENU",
            font=(FONT, 9, "bold"),
            text_color="#718BA6",
            anchor="w",
        ).grid(
            row=2,
            column=0,
            sticky="new",
            padx=32,
            pady=(27, 9),
        )

        nav = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        nav.grid(
            row=2,
            column=0,
            sticky="new",
            padx=20,
            pady=(51, 0),
        )
        nav.grid_columnconfigure(0, weight=1)

        items = [
            ("dashboard", "Tableau de bord", "dashboard"),
            ("clients", "Clients", "clients"),
            ("documents", "Documents", "documents"),
            ("settings", "Paramètres", "parametres"),
        ]

        for row, (key, label, icon_name) in enumerate(items):
            button = self._make_button(
                nav,
                label,
                icon_name,
                lambda page=key: self.on_navigate(page),
            )
            button.grid(
                row=row,
                column=0,
                sticky="ew",
                pady=(0, 4),
            )
            self.buttons[key] = button

    def _make_button(self, parent, label, icon_name, command):
        icon = load_icon(icon_name)

        if icon:
            self.icon_images.append(icon)

        button = ctk.CTkButton(
            parent,
            text=label,
            image=icon,
            compound="left",
            anchor="w",
            height=46,
            corner_radius=10,
            border_spacing=13,
            fg_color="transparent",
            hover_color=HOVER,
            text_color=MUTED,
            font=(FONT, 13, "normal"),
            command=command,
        )

        if icon:
            button.configure(
                compound="left",
                image=icon,
            )

        return button

    def _build_bottom(self):
        bottom = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        bottom.grid(
            row=3,
            column=0,
            sticky="sew",
            padx=20,
            pady=(12, 18),
        )
        bottom.grid_columnconfigure(0, weight=1)

        automation = ctk.CTkFrame(
            bottom,
            fg_color="#103247",
            border_width=1,
            border_color="#164B5B",
            corner_radius=12,
        )
        automation.grid(row=0, column=0, sticky="ew")
        automation.grid_columnconfigure(1, weight=1)

        symbol = ctk.CTkFrame(
            automation,
            width=36,
            height=36,
            corner_radius=8,
            fg_color="#145064",
        )
        symbol.grid(row=0, column=0, padx=(10, 9), pady=10)
        symbol.grid_propagate(False)

        ctk.CTkLabel(
            symbol,
            text="✦",
            font=(FONT, 18, "bold"),
            text_color="#45D9CE",
        ).place(relx=0.5, rely=0.5, anchor="center")

        status_text = ctk.CTkFrame(
            automation,
            fg_color="transparent",
        )
        status_text.grid(row=0, column=1, sticky="ew", pady=10)

        ctk.CTkLabel(
            status_text,
            text="Automatisation",
            font=(FONT, 10, "bold"),
            text_color="#E6F1F7",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            status_text,
            text="État à configurer",
            font=(FONT, 8),
            text_color="#8FA6BF",
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkFrame(
            automation,
            width=7,
            height=7,
            corner_radius=4,
            fg_color="#28D7A0",
        ).grid(row=0, column=2, padx=10)

        profile = ctk.CTkFrame(
            bottom,
            fg_color="transparent",
        )
        profile.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(15, 0),
            padx=7,
        )
        profile.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(
            profile,
            width=36,
            height=36,
            corner_radius=18,
            fg_color="#168FB8",
        ).grid(row=0, column=0, padx=(0, 10))

        avatar = ctk.CTkLabel(
            profile,
            text="U",
            font=(FONT, 10, "bold"),
            text_color=WHITE,
            fg_color="#168FB8",
            width=36,
            height=36,
            corner_radius=18,
        )
        avatar.place_forget()

        # Avatar textuel au-dessus du cercle
        avatar.grid(row=0, column=0, padx=(0, 10))

        user_text = ctk.CTkFrame(
            profile,
            fg_color="transparent",
        )
        user_text.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            user_text,
            text="Utilisateur",
            font=(FONT, 11, "bold"),
            text_color="#F4F8FB",
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            user_text,
            text="Compte local",
            font=(FONT, 9),
            text_color="#8FA6BF",
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkButton(
            profile,
            text="•••",
            width=24,
            height=25,
            fg_color="transparent",
            hover_color=HOVER,
            text_color="#8FA6BF",
            command=lambda: None,
        ).grid(row=0, column=2)

    def set_active(self, page_name):
        for key, button in self.buttons.items():
            is_active = key == page_name
            button.configure(
                fg_color=ACTIVE if is_active else "transparent",
                hover_color=ACTIVE if is_active else HOVER,
                text_color=WHITE if is_active else MUTED,
                font=(
                    FONT,
                    13,
                    "bold" if is_active else "normal",
                ),
            )
