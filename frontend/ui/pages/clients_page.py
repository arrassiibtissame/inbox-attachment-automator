
import customtkinter as ctk

from frontend.ui.components.page_header import PageHeader
from frontend.ui.components.search_bar import SearchBar
from frontend.ui.components.client_card import ClientCard
from frontend.ui.dialogs.client_form_dialog import ClientFormDialog
from frontend.ui.styles import colors, typography


class ClientsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.active_filter = "all"
        self.search_query = ""

        # Données temporaires de démonstration
        self.clients = [
            {
                "name": "Atlas Distribution SARL",
                "contact": "Contact principal",
                "email": "contact@atlas.example",
                "phone": "0612345678",
                "tax_id": "",
                "document_count": 24,
                "last_activity": "Aujourd'hui",
            },
            {
                "name": "Maroc Services",
                "contact": "Contact principal",
                "email": "contact@marocservices.example",
                "phone": "0623456789",
                "tax_id": "",
                "document_count": 18,
                "last_activity": "Hier",
            },
            {
                "name": "Bâtiment du Centre",
                "contact": "Contact principal",
                "email": "contact@batiment.example",
                "phone": "0634567890",
                "tax_id": "",
                "document_count": 12,
                "last_activity": "Il y a 2 jours",
            },
            {
                "name": "Comptoir du Nord",
                "contact": "Contact principal",
                "email": "contact@comptoir.example",
                "phone": "0645678901",
                "tax_id": "",
                "document_count": 31,
                "last_activity": "Aujourd'hui",
            },
        ]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # En-tête
        header = PageHeader(
            self,
            title="Clients",
            subtitle="Gérez vos clients et leurs documents centralisés.",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=32,
            pady=(30, 20),
        )

        # Barre de recherche et bouton d'ajout
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=32,
            pady=(0, 18),
        )
        toolbar.grid_columnconfigure(0, weight=1)

        self.search_bar = SearchBar(
            toolbar,
            placeholder="Rechercher par nom, contact, email, téléphone...",
            on_search=self.filter_clients,
            on_filter=self.show_filter_message,
        )
        self.search_bar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 12),
        )

        ctk.CTkButton(
            toolbar,
            text="+ Ajouter un client",
            height=44,
            corner_radius=10,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BUTTON_SIZE,
                weight="bold",
            ),
            command=self.open_add_client_form,
        ).grid(row=0, column=1)

        # Zone défilante des cartes
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.content.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=32,
            pady=(0, 24),
        )
        self.content.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="clients",
        )

        self.render_clients(self.clients)

    # --------------------------------------------------
    # AFFICHAGE DES CLIENTS
    # --------------------------------------------------

    def render_clients(self, clients):
        for widget in self.content.winfo_children():
            widget.destroy()

        if not clients:
            ctk.CTkLabel(
                self.content,
                text="Aucun client ne correspond à votre recherche.",
                font=ctk.CTkFont(size=14),
                text_color=colors.TEXT_SECONDARY,
            ).grid(
                row=0,
                column=0,
                columnspan=2,
                padx=12,
                pady=32,
            )
            return

        for index, client in enumerate(clients):
            row = index // 2
            column = index % 2

            card = ClientCard(
                self.content,
                name=client["name"],
                contact=client.get(
                    "contact",
                    "Contact non renseigné",
                ),
                phone=client.get("phone", ""),
                tax_id=client.get("tax_id", ""),
                email=client.get(
                    "email",
                    "Email non renseigné",
                ),
                document_count=client.get("document_count", 0),
                last_activity=client.get(
                    "last_activity",
                    "Aucune activité",
                ),
                on_open=lambda item=client: self.open_client_folder(item),
                on_edit=lambda item=client: self.open_edit_client_form(item),
                on_delete=lambda item=client: self.confirm_delete_client(item),
            )

            card.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=(0, 10) if column == 0 else (10, 0),
                pady=(0, 18),
            )

    # --------------------------------------------------
    # RECHERCHE ET FILTRES
    # --------------------------------------------------

    def filter_clients(self, query=""):
        self.search_query = query.strip()
        query_lower = self.search_query.casefold()

        filtered = []

        for client in self.clients:
            searchable_text = " ".join([
                str(client.get("name", "")),
                str(client.get("contact", "")),
                str(client.get("email", "")),
                str(client.get("phone", "")),
                str(client.get("tax_id", "")),
            ]).casefold()

            if query_lower and query_lower not in searchable_text:
                continue

            document_count = int(
                client.get("document_count", 0) or 0
            )

            if (
                self.active_filter == "with_documents"
                and document_count == 0
            ):
                continue

            if (
                self.active_filter == "without_documents"
                and document_count > 0
            ):
                continue

            filtered.append(client)

        self.render_clients(filtered)

    def show_filter_message(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Filtrer les clients")
        dialog.geometry("340x280")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=colors.SURFACE)

        ctk.CTkLabel(
            dialog,
            text="Filtrer les clients",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=22, pady=(22, 5))

        ctk.CTkLabel(
            dialog,
            text="Choisissez les clients à afficher.",
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_SECONDARY,
        ).pack(anchor="w", padx=22, pady=(0, 16))

        filter_var = ctk.StringVar(value=self.active_filter)

        options = [
            ("all", "Tous les clients"),
            ("with_documents", "Avec documents"),
            ("without_documents", "Sans documents"),
        ]

        for value, label in options:
            ctk.CTkRadioButton(
                dialog,
                text=label,
                variable=filter_var,
                value=value,
                radiobutton_width=18,
                radiobutton_height=18,
                fg_color=colors.PRIMARY,
                hover_color=colors.PRIMARY_HOVER,
                text_color=colors.TEXT_PRIMARY,
            ).pack(anchor="w", padx=24, pady=8)

        def apply_filter():
            self.active_filter = filter_var.get()
            self.filter_clients(self.search_query)
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text="Appliquer les filtres",
            height=38,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=apply_filter,
        ).pack(fill="x", padx=22, pady=(18, 22))

    # --------------------------------------------------
    # AJOUT ET MODIFICATION
    # --------------------------------------------------

    def open_add_client_form(self):
        self.open_client_form()

    def open_edit_client_form(self, client):
        self.open_client_form(client)

    def open_client_form(self, client=None):
        is_editing = client is not None

        def save_client(data):
            name = data["name"].strip()
            tax_id = data.get("tax_id", "").strip()

            # Vérifier les doublons en excluant le client modifié
            for existing_client in self.clients:
                if existing_client is client:
                    continue

                if (
                    existing_client["name"].strip().casefold()
                    == name.casefold()
                ):
                    dialog.message.configure(
                        text="Cette société existe déjà dans la liste."
                    )
                    return

                existing_tax_id = existing_client.get(
                    "tax_id", ""
                ).strip()

                if (
                    tax_id
                    and existing_tax_id
                    and existing_tax_id.casefold() == tax_id.casefold()
                ):
                    dialog.message.configure(
                        text="Cet identifiant fiscal existe déjà."
                    )
                    return

            if is_editing:
                client.update(data)
            else:
                data["document_count"] = 0
                data["last_activity"] = "Aucune activité"
                self.clients.append(data)

            # Fermer le formulaire après un enregistrement valide
            dialog.destroy()

            # Réinitialiser recherche et filtres
            self.active_filter = "all"
            self.search_query = ""
            self.search_bar.search_input.delete(0, "end")

            self.filter_clients("")

        dialog = ClientFormDialog(
            self,
            on_save=save_client,
            client=client,
        )

    # --------------------------------------------------
    # OUVRIR LES INFORMATIONS DU CLIENT
    # --------------------------------------------------

    def open_client_folder(self, client):
        dialog = ctk.CTkToplevel(self)
        dialog.title(client["name"])
        dialog.geometry("420x280")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=colors.SURFACE)

        ctk.CTkLabel(
            dialog,
            text=client["name"],
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
            wraplength=360,
        ).pack(padx=24, pady=(28, 12))

        ctk.CTkLabel(
            dialog,
            text=(
                f'{client.get("document_count", 0)} document(s)\n'
                f'Dernière activité : {client.get("last_activity", "Aucune activité")}\n'
                f'Identifiant fiscal : {client.get("tax_id") or "Non renseigné"}\n'
                f'Téléphone : {client.get("phone") or "Non renseigné"}'
            ),
            text_color=colors.TEXT_SECONDARY,
            justify="center",
            wraplength=360,
        ).pack(padx=24, pady=8)

        ctk.CTkButton(
            dialog,
            text="Fermer",
            command=dialog.destroy,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
        ).pack(pady=18)

    # --------------------------------------------------
    # SUPPRESSION
    # --------------------------------------------------

    def confirm_delete_client(self, client):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirmer la suppression")
        dialog.geometry("430x240")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="Supprimer ce client ?",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(
            row=0,
            column=0,
            padx=24,
            pady=(24, 10),
        )

        ctk.CTkLabel(
            dialog,
            text=(
                f'Voulez-vous retirer « {client["name"]} » de la liste ?\n'
                "Les documents ne seront pas supprimés."
            ),
            text_color=colors.TEXT_SECONDARY,
            wraplength=370,
            justify="center",
        ).grid(
            row=1,
            column=0,
            padx=24,
            pady=8,
        )

        actions = ctk.CTkFrame(
            dialog,
            fg_color="transparent",
        )
        actions.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=24,
            pady=18,
        )
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            actions,
            text="Annuler",
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            command=dialog.destroy,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )

        def delete_client():
            if client in self.clients:
                self.clients.remove(client)

            self.filter_clients(self.search_query)
            dialog.destroy()

        ctk.CTkButton(
            actions,
            text="Confirmer la suppression",
            fg_color=colors.ERROR,
            hover_color="#B8323B",
            command=delete_client,
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )
