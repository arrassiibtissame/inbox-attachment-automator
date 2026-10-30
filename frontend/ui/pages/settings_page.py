
import customtkinter as ctk

from pathlib import Path
from tkinter import filedialog

from frontend.ui.components.page_header import PageHeader
from frontend.ui.styles import colors, typography


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, gmail_monitor):
        super().__init__(parent, fg_color="transparent")

        self.gmail_monitor = gmail_monitor
        self.connected = False

        # Dossier de téléchargement par défaut du backend.
        from backend import download_attachments as downloader

        self.download_dir = Path(downloader.DOWNLOAD_DIR)

        self.grid_columnconfigure(0, weight=1)

        header = PageHeader(
            self,
            title="Paramètres",
            subtitle="Configurez les préférences de FIDOMEK ONE",
        )
        header.grid(
            row=0, column=0, sticky="ew",
            padx=32, pady=(30, 24)
        )

        # =========================
        # APPARENCE
        # =========================

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
            text="Choisissez le thème visuel de l'application.",
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 12))

        self.theme_option = ctk.CTkOptionMenu(
            appearance_card,
            values=["Clair", "Sombre", "Système"],
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

        # =========================
        # STOCKAGE
        # =========================

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
            text="Choisissez où enregistrer les pièces jointes téléchargées.",
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 12))

        storage_frame = ctk.CTkFrame(
            storage_card,
            fg_color="transparent",
        )
        storage_frame.grid(
            row=2, column=0, sticky="ew",
            padx=22, pady=(0, 20)
        )
        storage_frame.grid_columnconfigure(0, weight=1)

        self.folder_label = ctk.CTkLabel(
            storage_frame,
            text=str(self.download_dir),
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_SECONDARY,
            anchor="w",
            wraplength=650,
        )
        self.folder_label.grid(
            row=0, column=0, sticky="ew", padx=(0, 12)
        )

        self.browse_button = ctk.CTkButton(
            storage_frame,
            text="Parcourir",
            width=110,
            command=self.choose_download_folder,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
        )
        self.browse_button.grid(
            row=0, column=1, sticky="e"
        )

        # =========================
        # INTÉGRATION GMAIL
        # =========================

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
            text="Connexion à la messagerie",
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
                "Surveillez la boîte Gmail autorisée du cabinet "
                "et récupérez automatiquement les pièces jointes."
            ),
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
            wraplength=650,
            justify="left",
        ).grid(
            row=1, column=0, sticky="w",
            padx=22, pady=(0, 16)
        )

        # Informations de statut.
        status_frame = ctk.CTkFrame(
            gmail_card,
            fg_color="transparent",
        )
        status_frame.grid(
            row=2, column=0, sticky="ew",
            padx=22, pady=(0, 14)
        )

        self.connection_label = ctk.CTkLabel(
            status_frame,
            text="Connexion Gmail : non connectée",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors.TEXT_SECONDARY,
        )
        self.connection_label.pack(anchor="w")

        self.monitor_label = ctk.CTkLabel(
            status_frame,
            text="Surveillance : arrêtée",
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
        )
        self.monitor_label.pack(anchor="w", pady=(7, 0))

        self.activity_label = ctk.CTkLabel(
            status_frame,
            text="En attente de démarrage.",
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_MUTED,
            wraplength=650,
            justify="left",
        )
        self.activity_label.pack(anchor="w", pady=(7, 0))

        # Boutons de contrôle.
        buttons_frame = ctk.CTkFrame(
            gmail_card,
            fg_color="transparent",
        )
        buttons_frame.grid(
            row=3, column=0, sticky="w",
            padx=22, pady=(0, 20)
        )

        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="Démarrer la surveillance",
            command=self.start_monitoring,
            fg_color=colors.SUCCESS,
            hover_color="#126B53",
            width=190,
        )
        self.start_button.pack(side="left", padx=(0, 10))

        self.stop_button = ctk.CTkButton(
            buttons_frame,
            text="Arrêter",
            command=self.stop_monitoring,
            fg_color=colors.ERROR,
            hover_color="#B83240",
            width=100,
            state="disabled",
        )
        self.stop_button.pack(side="left")

        # Actualiser les événements du backend sans bloquer l'interface.
        self.after(500, self.poll_gmail_events)

    # =========================
    # STOCKAGE
    # =========================

    def choose_download_folder(self):
        """Permettre à l'utilisateur de choisir le dossier."""

        if self.gmail_monitor.is_running:
            self.activity_label.configure(
                text="Arrêtez la surveillance avant de changer de dossier."
            )
            return

        selected_folder = filedialog.askdirectory(
            title="Choisir le dossier de téléchargement",
            initialdir=str(self.download_dir),
        )

        if not selected_folder:
            return

        self.download_dir = Path(selected_folder)

        self.folder_label.configure(
            text=str(self.download_dir)
        )

        self.activity_label.configure(
            text="Dossier de destination mis à jour."
        )

    # =========================
    # SURVEILLANCE GMAIL
    # =========================

    def start_monitoring(self):
        """Démarrer la surveillance en arrière-plan."""

        if self.gmail_monitor.is_running:
            return

        started = self.gmail_monitor.start(
            download_dir=str(self.download_dir)
        )

        if started:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.browse_button.configure(state="disabled")

            self.monitor_label.configure(
                text="Surveillance : démarrage...",
                text_color=colors.WARNING,
            )

    def stop_monitoring(self):
        """Demander l'arrêt de la surveillance."""

        stopped = self.gmail_monitor.stop()

        if stopped:
            self.stop_button.configure(state="disabled")
            self.activity_label.configure(
                text="Arrêt de la surveillance demandé..."
            )

    # =========================
    # ÉVÉNEMENTS DU BACKEND
    # =========================

    def poll_gmail_events(self):
        """Lire les événements envoyés par le thread Gmail."""

        for event in self.gmail_monitor.get_events():
            event_type = event["type"]
            message = event["message"]

            self.activity_label.configure(text=message)

            if event_type == "connected":
                self.connected = True

                self.connection_label.configure(
                    text="Connexion Gmail : connectée",
                    text_color=colors.SUCCESS,
                )

            elif event_type == "error":
                self.connected = False

                self.connection_label.configure(
                    text="Connexion Gmail : erreur",
                    text_color=colors.ERROR,
                )

                self.monitor_label.configure(
                    text="Surveillance : erreur",
                    text_color=colors.ERROR,
                )

            elif event_type == "status":
                self.monitor_label.configure(
                    text="Surveillance : active",
                    text_color=colors.SUCCESS,
                )

            elif event_type == "stopped":
                self.monitor_label.configure(
                    text="Surveillance : arrêtée",
                    text_color=colors.TEXT_SECONDARY,
                )

                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.browse_button.configure(state="normal")

                if not self.connected:
                    self.connection_label.configure(
                        text="Connexion Gmail : non connectée",
                        text_color=colors.TEXT_SECONDARY,
                    )

        # Continuer à vérifier les événements.
        self.after(500, self.poll_gmail_events)

    # =========================
    # APPARENCE
    # =========================

    @staticmethod
    def change_theme(choice):
        themes = {
            "Clair": "light",
            "Sombre": "dark",
            "Système": "system",
        }

        ctk.set_appearance_mode(themes[choice])
