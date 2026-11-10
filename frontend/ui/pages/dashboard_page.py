
import customtkinter as ctk

from frontend.ui.components.page_header import PageHeader
from frontend.ui.components.stat_card import StatCard
from frontend.ui.styles import colors, typography

from backend.download_attachments import (
    initialize_database,
    get_downloaded_documents,
)


class DashboardPage(ctk.CTkFrame):
    """Page principale de suivi de FIDOMEK ONE."""

    REFRESH_INTERVAL = 5000
    RECENT_DOCUMENTS_LIMIT = 5

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=colors.BACKGROUND,
            corner_radius=0,
        )

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._refresh_job = None

        # Initialisation de la base de données
        try:
            initialize_database()
        except Exception as error:
            print(f"Erreur d'initialisation SQLite : {error}")

        # En-tête
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

        self.documents_card = StatCard(
            stats_frame,
            title="Documents reçus",
            value="0",
            subtitle="Documents importés",
            accent_color=colors.PRIMARY,
        )
        self.documents_card.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10),
        )

        self.clients_card = StatCard(
            stats_frame,
            title="Clients",
            value="—",
            subtitle="Gestion clients à connecter",
            accent_color=colors.ACCENT_PURPLE,
        )
        self.clients_card.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=10,
        )

        self.pending_card = StatCard(
            stats_frame,
            title="À vérifier",
            value="0",
            subtitle="Documents à contrôler",
            accent_color=colors.WARNING,
        )
        self.pending_card.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(10, 0),
        )

        # État de l'automatisation e-mail
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

        self.gmail_status_label = ctk.CTkLabel(
            automation_frame,
            text="Connexion Gmail : état non vérifié",
            font=(typography.FONT_FAMILY, typography.BODY_SIZE),
            text_color=colors.TEXT_SECONDARY,
        )
        self.gmail_status_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 5),
        )

        ctk.CTkLabel(
            automation_frame,
            text="Téléchargement automatique : géré par le backend",
            font=(typography.FONT_FAMILY, typography.BODY_SIZE),
            text_color=colors.TEXT_SECONDARY,
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=24,
            pady=(0, 18),
        )

        # Documents récents
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

        # Premier chargement
        self.refresh_dashboard()

        # Actualisation périodique
        self._schedule_refresh()

        # Arrêter les actualisations lorsque la page est détruite
        self.bind("<Destroy>", self._on_destroy, add="+")

    def refresh_dashboard(self):
        """Récupérer les données réelles depuis SQLite."""

        try:
            documents = get_downloaded_documents()

            total_documents = len(documents)

            documents_a_verifier = sum(
                1
                for document in documents
                if document.get("status") == "À vérifier"
            )

            self.documents_card.set_value(total_documents)
            self.pending_card.set_value(documents_a_verifier)

            self._display_recent_documents(documents)

        except Exception as error:
            print(f"Erreur de chargement du tableau de bord : {error}")
            self.gmail_status_label.configure(
                text="Données indisponibles : vérifier la base de données"
            )

    def _display_recent_documents(self, documents):
        """Afficher les cinq derniers documents téléchargés."""

        for widget in self.recent_list.winfo_children():
            widget.destroy()

        recent_documents = documents[:self.RECENT_DOCUMENTS_LIMIT]

        if not recent_documents:
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

        for index, document in enumerate(recent_documents):
            name = document.get("name", "Document sans nom")
            date = document.get("date", "Date inconnue")
            document_type = document.get("type", "Autre")
            status = document.get("status", "À vérifier")

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
                text=f"{document_type}  •  {date}  •  {status}",
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
        """Annuler le rafraîchissement si la page est détruite."""

        if event.widget is self and self._refresh_job is not None:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass

            self._refresh_job = None
