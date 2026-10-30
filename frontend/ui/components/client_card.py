
import customtkinter as ctk

from frontend.ui.styles import colors
from frontend.ui.components.client_card_header import ClientCardHeader
from frontend.ui.components.client_info_section import ClientInfoSection
from frontend.ui.components.client_activity import ClientActivity
from frontend.ui.components.client_card_actions import ClientCardActions


class ClientCard(ctk.CTkFrame):
    """Card displaying a client's information and available actions."""

    def __init__(
        self,
        parent,
        name,
        contact="Contact non renseigné",
        phone="",
        tax_id="",
        email="Email non renseigné",
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
        )

        self.grid_columnconfigure(0, weight=1)

        # 1. En-tête : avatar, nom et nombre de documents
        self.header = ClientCardHeader(
            self,
            name=name,
            document_count=document_count,
        )
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=16,
            pady=(18, 12),
        )

        # 2. Informations du client
        self.info_section = ClientInfoSection(
            self,
            contact=contact,
            phone=phone,
            tax_id=tax_id,
            email=email,
        )
        self.info_section.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 12),
        )

        # Séparateur
        ctk.CTkFrame(
            self,
            height=1,
            fg_color=colors.BORDER,
        ).grid(
            row=2,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 12),
        )

        # 3. Dernière activité
        self.activity = ClientActivity(
            self,
            last_activity=last_activity,
        )
        self.activity.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 14),
        )

        # 4. Actions
        self.actions = ClientCardActions(
            self,
            on_open=on_open,
            on_edit=on_edit,
            on_delete=on_delete,
        )
        self.actions.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=16,
            pady=(0, 16),
        )
