
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientCard(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        name,
        contact="Contact non renseigné",
        email="Email non renseigné",
        document_count=0,
        last_activity="Aucune activité",
        on_open=None,
         on_delete=None,
    ):
        super().__init__(
            parent,
            fg_color=colors.SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=colors.BORDER,
        )

        self.grid_columnconfigure(1, weight=1)

        # Avatar avec l'initiale du client
        initial = name[0].upper() if name else "?"

        ctk.CTkLabel(
            self,
            text=initial,
            width=46,
            height=46,
            corner_radius=13,
            fg_color=colors.PRIMARY_LIGHT,
            text_color=colors.PRIMARY,
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(
            row=0, column=0, sticky="nw",
            padx=(16, 12), pady=(18, 10),
        )

        # Informations du client
        details = ctk.CTkFrame(self, fg_color="transparent")
        details.grid(
            row=0, column=1, sticky="ew",
            padx=(0, 14), pady=(18, 8),
        )
        details.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            details,
            text=name,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=15,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
            anchor="w",
            wraplength=230,
        ).grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            details,
            text=contact,
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", pady=(5, 0))

        ctk.CTkLabel(
            details,
            text=email,
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_MUTED,
            anchor="w",
            wraplength=230,
        ).grid(row=2, column=0, sticky="ew", pady=(3, 0))

        # Séparateur
        ctk.CTkFrame(
            self,
            height=1,
            fg_color=colors.BORDER,
        ).grid(
            row=1, column=0, columnspan=2,
            sticky="ew", padx=16, pady=(8, 12),
        )

        ctk.CTkLabel(
            self,
            text=f"{document_count} document(s)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
            anchor="w",
        ).grid(
            row=2, column=0, columnspan=2,
            sticky="ew", padx=16, pady=(0, 5),
        )

        ctk.CTkLabel(
            self,
            text=f"Dernière activité : {last_activity}",
            font=ctk.CTkFont(size=11),
            text_color=colors.TEXT_MUTED,
            anchor="w",
            wraplength=300,
        ).grid(
            row=3, column=0, columnspan=2,
            sticky="ew", padx=16, pady=(0, 12),
        )
       
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(
            row=4, column=0, columnspan=2,
            sticky="ew", padx=16, pady=(0, 16),
        )
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            actions,
            text="Ouvrir le dossier",
            height=34,
            corner_radius=8,
            fg_color=colors.PRIMARY_LIGHT,
            hover_color=colors.ACCENT_LIGHT,
            text_color=colors.PRIMARY,
            command=on_open if on_open else lambda: None,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            actions,
            text="Supprimer",
            height=34,
            corner_radius=8,
            fg_color=colors.ERROR_LIGHT,
            hover_color="#F8D7DA",
            text_color=colors.ERROR,
            command=on_delete if on_delete else lambda: None,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
