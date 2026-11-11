import customtkinter as ctk

from backend.database.connection import SessionLocal
from backend.services.dashboard_service import DashboardService

from frontend.ui.components.page_header import PageHeader
from frontend.ui.components.stat_card import StatCard
from frontend.ui.styles import colors, typography


class DashboardPage(ctk.CTkFrame):
    """Tableau de bord dynamique de FIDOMEK ONE."""

    REFRESH_INTERVAL = 5000
    RECENT_DOCUMENTS_LIMIT = 5

    def __init__(self, parent, current_user=None, on_processing_click=None):
        super().__init__(
            parent,
            fg_color=colors.BACKGROUND,
            corner_radius=0,
        )

        self.current_user = current_user
        self.on_processing_click = on_processing_click
        self.processing_document_ids = {}
        self._refresh_job = None
        self.stats_cards = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        header = PageHeader(
            self,
            title="Tableau de bord",
            subtitle="Vue générale de l'activité du cabinet",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=30,
            pady=(25, 20),
        )

        # Six indicateurs répartis sur deux lignes.
        stats_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        stats_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 20),
        )

        for column in range(3):
            stats_frame.grid_columnconfigure(column, weight=1)

        cards_config = [
            (
                "active_clients",
                "Clients actifs",
                "Portefeuille clients",
                colors.PRIMARY,
            ),
            (
                "documents_received",
                "Documents reçus",
                "Documents enregistrés",
                colors.ACCENT_PURPLE,
            ),
            (
                "documents_to_review",
                "À vérifier",
                "Documents en attente",
                colors.WARNING,
            ),
            (
                "classified_documents",
                "Documents classés",
                "Documents traités",
                colors.PRIMARY,
            ),
            (
                "gmail_received",
                "Gmail",
                "Documents reçus par e-mail",
                colors.ACCENT_PURPLE,
            ),
            (
                "whatsapp_received",
                "WhatsApp",
                "Documents reçus par WhatsApp",
                colors.WARNING,
            ),
        ]

        for index, (key, title, subtitle, accent) in enumerate(cards_config):
            card = StatCard(
                stats_frame,
                title=title,
                value="0",
                subtitle=subtitle,
                accent_color=accent,
            )
            card.grid(
                row=index // 3,
                column=index % 3,
                sticky="ew",
                padx=6,
                pady=6,
            )
            self.stats_cards[key] = card

        # Informations sur les réceptions.
        reception_frame = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        reception_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 20),
        )
        reception_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            reception_frame,
            text="Suivi des réceptions",
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

        self.reception_info_label = ctk.CTkLabel(
            reception_frame,
            text=(
                "Les compteurs Gmail et WhatsApp reflètent "
                "les documents enregistrés dans le système."
            ),
            font=(typography.FONT_FAMILY, typography.BODY_SIZE),
            text_color=colors.TEXT_SECONDARY,
            anchor="w",
        )
        self.reception_info_label.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=24,
            pady=(0, 18),
        )

        # Documents à traiter.
        processing_frame = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        processing_frame.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 20),
        )
        processing_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            processing_frame,
            text="Documents à traiter",
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
            pady=(18, 12),
        )

        processing_cards_frame = ctk.CTkFrame(
            processing_frame,
            fg_color="transparent",
        )
        processing_cards_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=18,
            pady=(0, 18),
        )

        self.processing_values = {}

        processing_config = [
            ("unidentified", "Non identifiés", colors.WARNING),
            ("awaiting_validation", "À valider", colors.ACCENT_PURPLE),
            ("overdue", "En retard", colors.WARNING),
            ("claimed", "Pris en charge", colors.PRIMARY),
        ]

        for column in range(4):
            processing_cards_frame.grid_columnconfigure(
                column,
                weight=1,
            )

        for index, (key, title, accent) in enumerate(processing_config):
            item_frame = ctk.CTkFrame(
                processing_cards_frame,
                fg_color=colors.BACKGROUND,
                corner_radius=12,
                border_width=1,
                border_color=colors.BORDER,
            )
            item_frame.grid(
                row=0,
                column=index,
                sticky="ew",
                padx=5,
                pady=4,
            )

            ctk.CTkLabel(
                item_frame,
                text=title,
                font=(
                    typography.FONT_FAMILY,
                    typography.CAPTION_SIZE,
                ),
                text_color=colors.TEXT_SECONDARY,
            ).pack(
                anchor="w",
                padx=14,
                pady=(12, 2),
            )

            value_label = ctk.CTkLabel(
                item_frame,
                text="0",
                font=(
                    typography.FONT_FAMILY,
                    typography.SECTION_TITLE_SIZE + 4,
                    "bold",
                ),
                text_color=accent,
            )
            value_label.pack(
                anchor="w",
                padx=14,
                pady=(0, 12),
            )

            self.processing_values[key] = value_label
            item_frame.bind(
                '<Button-1>',
                lambda event, category=key: self._open_processing_category(category),
            )
            for widget in item_frame.winfo_children():
                widget.bind(
                    '<Button-1>',
                    lambda event, category=key: self._open_processing_category(category),
                )
        # Documents récents.
        recent_frame = ctk.CTkFrame(
            self,
            fg_color=colors.SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=colors.BORDER,
        )
        recent_frame.grid(
            row=4,
            column=0,
            sticky="nsew",
            padx=30,
            pady=(0, 30),
        )
        recent_frame.grid_columnconfigure(0, weight=1)
        recent_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            recent_frame,
            text="Documents récents",
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

        self.recent_list = ctk.CTkFrame(
            recent_frame,
            fg_color="transparent",
        )
        self.recent_list.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=24,
            pady=(5, 20),
        )
        self.recent_list.grid_columnconfigure(0, weight=1)

        self.refresh_dashboard()
        self._schedule_refresh()
        self.bind("<Destroy>", self._on_destroy, add="+")

    def refresh_dashboard(self):
        """Charger les statistiques depuis la base SQLAlchemy."""

        if self.current_user is None:
            self.reception_info_label.configure(
                text="Aucun utilisateur connecté."
            )
            return

        try:
            with SessionLocal() as session:
                service = DashboardService(session)
                dashboard_data = service.get_dashboard_data(
                    self.current_user,
                    recent_limit=self.RECENT_DOCUMENTS_LIMIT,
                )

            statistics = dashboard_data["statistics"]

            for key, card in self.stats_cards.items():
                card.set_value(statistics.get(key, 0))

            self._display_documents_to_process(
                dashboard_data.get("documents_to_process", {})
            )

            self._display_recent_documents(
                dashboard_data["recent_documents"]
            )

            self.reception_info_label.configure(
                text="Données actualisées depuis la base de données."
            )

        except Exception as error:
            print(
                f"Erreur de chargement du tableau de bord : {error}"
            )
            self.reception_info_label.configure(
                text="Données indisponibles : vérifier la base de données."
            )

    def _display_documents_to_process(self, data):
        """Actualiser les compteurs et m?moriser les documents associ?s."""

        self.processing_document_ids = {}

        for key, label in self.processing_values.items():
            items = data.get(key, [])
            self.processing_document_ids[key] = [
                item.get("document_id")
                for item in items
                if item.get("document_id") is not None
            ]
            label.configure(text=str(len(items)))

    def _open_processing_category(self, category):
        """Ouvrir les documents associ?s ? une cat?gorie du tableau de bord."""

        if self.on_processing_click is None:
            return

        document_ids = self.processing_document_ids.get(category, [])
        self.on_processing_click(category, document_ids)

    def _display_recent_documents(self, documents):
        """Afficher les derniers documents accessibles à l'utilisateur."""

        for widget in self.recent_list.winfo_children():
            widget.destroy()

        if not documents:
            ctk.CTkLabel(
                self.recent_list,
                text="Aucun document pour le moment.",
                font=(
                    typography.FONT_FAMILY,
                    typography.BODY_SIZE,
                ),
                text_color=colors.TEXT_SECONDARY,
            ).grid(
                row=0,
                column=0,
                sticky="w",
                pady=15,
            )
            return

        status_labels = {
            "TO_REVIEW": "À vérifier",
            "CLASSIFIED": "Classé",
        }

        source_labels = {
            "GMAIL": "Gmail",
            "WHATSAPP": "WhatsApp",
            "MANUAL": "Manuel",
        }

        for index, document in enumerate(documents):
            name = document.get("name") or "Document sans nom"
            document_type = document.get("type") or "Autre"
            status = status_labels.get(
                document.get("status"),
                document.get("status", "Inconnu"),
            )
            source = source_labels.get(
                document.get("source"),
                document.get("source", "Inconnue"),
            )

            date_value = document.get("date")
            if hasattr(date_value, "strftime"):
                date_text = date_value.strftime("%d/%m/%Y %H:%M")
            else:
                date_text = str(date_value or "Date inconnue")

            client_name = document.get("client_name")
            details = f"{document_type}  •  {date_text}  •  {status}  •  {source}"

            if client_name:
                details += f"  •  {client_name}"

            document_frame = ctk.CTkFrame(
                self.recent_list,
                fg_color="transparent",
            )
            document_frame.grid(
                row=index,
                column=0,
                sticky="ew",
                pady=5,
            )
            document_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                document_frame,
                text=name,
                font=(
                    typography.FONT_FAMILY,
                    typography.BODY_SIZE,
                ),
                text_color=colors.TEXT_PRIMARY,
                anchor="w",
            ).grid(
                row=0,
                column=0,
                sticky="ew",
            )

            ctk.CTkLabel(
                document_frame,
                text=details,
                font=(
                    typography.FONT_FAMILY,
                    typography.CAPTION_SIZE,
                ),
                text_color=colors.TEXT_SECONDARY,
                anchor="w",
            ).grid(
                row=1,
                column=0,
                sticky="w",
            )

    def _schedule_refresh(self):
        """Programmer le prochain rafraîchissement."""

        self._refresh_job = self.after(
            self.REFRESH_INTERVAL,
            self._refresh_and_reschedule,
        )

    def _refresh_and_reschedule(self):
        self.refresh_dashboard()
        self._schedule_refresh()

    def _on_destroy(self, event):
        """Annuler le rafraîchissement lorsque la page est détruite."""

        if event.widget is self and self._refresh_job is not None:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass

            self._refresh_job = None
