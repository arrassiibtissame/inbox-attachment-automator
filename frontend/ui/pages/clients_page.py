import customtkinter as ctk
from types import SimpleNamespace
from sqlalchemy.exc import IntegrityError

from frontend.ui.components.page_header import PageHeader
from frontend.ui.components.search_bar import SearchBar
from frontend.ui.components.client_card import ClientCard
from frontend.ui.dialogs.client_form_dialog import ClientFormDialog
from frontend.ui.dialogs.client_detail_dialog import ClientDetailDialog
from frontend.ui.styles import colors, typography

from backend.database.connection import SessionLocal
from backend.database.models.user import UserRole
from backend.services.client_service import ClientService


class ClientsPage(ctk.CTkFrame):

    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color="transparent")

        self.current_user = current_user
        self.is_admin = current_user.role == UserRole.ADMIN

        self.active_filter = "all"
        self.status_filter = "active"
        self.search_query = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = PageHeader(
            self,
            title="Clients",
            subtitle="Gérez vos clients et leurs documents centralisés.",
        )
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=32,
            pady=(30, 20),
        )

        toolbar = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
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
            placeholder="Rechercher par nom, code, ICE, IF, contact...",
            on_search=self.filter_clients,
            on_filter=self.show_filter_message,
        )
        self.search_bar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 12),
        )

        self.status_filter_button = ctk.CTkButton(
            toolbar,
            text="Statut : Actifs",
            height=44,
            width=135,
            corner_radius=10,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.show_status_filter_dialog,
        )
        self.status_filter_button.grid(
            row=0, column=1, padx=(0, 10)
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
        ).grid(row=0, column=2)

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

        self.current_page = 1
        self.page_size = 30
        self.total_clients = 0
        self.total_pages = 1

        self.pagination_bar = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        self.pagination_bar.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=32,
            pady=(0, 14),
        )
        self.pagination_bar.grid_columnconfigure(1, weight=1)

        self.previous_page_button = ctk.CTkButton(
            self.pagination_bar,
            text="? Pr?c?dent",
            width=110,
            height=34,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            command=lambda: self.change_page(-1),
        )
        self.previous_page_button.grid(row=0, column=0, sticky="w")

        self.pagination_label = ctk.CTkLabel(
            self.pagination_bar,
            text="Page 1 / 1 ? 0 client",
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_SECONDARY,
        )
        self.pagination_label.grid(row=0, column=1, padx=12)

        self.next_page_button = ctk.CTkButton(
            self.pagination_bar,
            text="Suivant ?",
            width=110,
            height=34,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            command=lambda: self.change_page(1),
        )
        self.next_page_button.grid(row=0, column=2, sticky="e")

        self._display_current_page()

    # --------------------------------------------------
    # CHARGEMENT DEPUIS LA BASE DE DONNEES
    # --------------------------------------------------

    def _load_clients(self):
        session = SessionLocal()

        try:
            service = ClientService(session)

            rows, total = service.list_clients_page(
                self.current_user,
                page=self.current_page,
                page_size=self.page_size,
                status=self.status_filter,
                document_filter=self.active_filter,
                search=self.search_query,
            )

            result = []

            for client, document_count in rows:
                responsible = client.responsible_user

                result.append({
                    "id": client.id,
                    "name": client.company_name or "",
                    "internal_code": client.internal_code or "",
                    "ice": client.ice or "",
                    "tax_id": client.ice or "",
                    "if_number": client.if_number or "",
                    "cnss_number": client.cnss_number or "",
                    "rc_number": client.rc_number or "",
                    "rc_city": client.rc_city or "",
                    "patente": client.patente or "",
                    "address": client.address or "",
                    "contact": client.contact_name or "",
                    "email": client.email or "",
                    "phone": client.phone_number or "",
                    "responsible_user_id": client.responsible_user_id,
                    "responsible_name": (
                        responsible.full_name
                        if responsible
                        else "Non attribu?"
                    ),
                    "is_active": bool(client.is_active),
                    "document_count": int(document_count),
                    "last_activity": "Aucune activit?",
                })

            return result, total

        finally:
            session.close()

    def _display_current_page(self):
        self.clients, self.total_clients = self._load_clients()

        self.total_pages = max(
            1,
            (self.total_clients + self.page_size - 1) // self.page_size,
        )

        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
            self.clients, self.total_clients = self._load_clients()

        self.render_clients(self.clients)

        self.pagination_label.configure(
            text=(
                f"Page {self.current_page} / {self.total_pages}"
                f" ? {self.total_clients} client(s)"
            )
        )

        self.previous_page_button.configure(
            state="normal" if self.current_page > 1 else "disabled"
        )
        self.next_page_button.configure(
            state=(
                "normal"
                if self.current_page < self.total_pages
                else "disabled"
            )
        )

    def change_page(self, direction):
        target_page = self.current_page + direction

        if 1 <= target_page <= self.total_pages:
            self.current_page = target_page
            self._display_current_page()

    def _refresh_clients(self):
        self.current_page = 1
        self._display_current_page()

    # --------------------------------------------------
    # AFFICHAGE
    # --------------------------------------------------

    def render_clients(self, clients):
        for widget in self.content.winfo_children():
            widget.destroy()

        if not clients:
            ctk.CTkLabel(
                self.content,
                text="Aucun client ne correspond ? votre recherche.",
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
            is_archived = not client["is_active"]

            card = ClientCard(
                self.content,
                name=client["name"],
                contact=client["contact"],
                phone=client["phone"],
                tax_id=client["ice"],
                email=client["email"],
                responsible_name=client["responsible_name"],
                document_count=client["document_count"],
                last_activity=client["last_activity"],
                is_archived=is_archived,
                on_open=lambda item=client: self.open_client_folder(item),
                on_edit=(
                    None if is_archived
                    else lambda item=client: self.open_edit_client_form(item)
                ),
                on_delete=(
                    None if is_archived
                    else lambda item=client: self.confirm_delete_client(item)
                ),
                on_restore=(
                    (lambda item=client: self.confirm_restore_client(item))
                    if is_archived else None
                ),
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
        self.current_page = 1
        self._display_current_page()

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

    def show_status_filter_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Statut des clients")
        dialog.geometry("350x300")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=colors.SURFACE)

        ctk.CTkLabel(
            dialog,
            text="Statut des clients",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=22, pady=(22, 5))

        ctk.CTkLabel(
            dialog,
            text="Choisissez les clients ? afficher.",
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_SECONDARY,
        ).pack(anchor="w", padx=22, pady=(0, 16))

        status_var = ctk.StringVar(value=self.status_filter)

        options = [
            ("active", "Actifs"),
            ("archived", "Archiv?s"),
            ("all", "Tous les clients"),
        ]

        for value, label in options:
            ctk.CTkRadioButton(
                dialog,
                text=label,
                variable=status_var,
                value=value,
                radiobutton_width=18,
                radiobutton_height=18,
                fg_color=colors.PRIMARY,
                hover_color=colors.PRIMARY_HOVER,
                text_color=colors.TEXT_PRIMARY,
            ).pack(anchor="w", padx=24, pady=8)

        def apply_status():
            self.status_filter = status_var.get()

            labels = {
                "active": "Statut : Actifs",
                "archived": "Statut : Archiv?s",
                "all": "Statut : Tous",
            }
            self.status_filter_button.configure(
                text=labels[self.status_filter]
            )
            self.filter_clients(self.search_query)
            dialog.destroy()

        ctk.CTkButton(
            dialog,
            text="Appliquer",
            height=38,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=apply_status,
        ).pack(fill="x", padx=22, pady=(18, 22))

    # --------------------------------------------------
    # AJOUT ET MODIFICATION
    # --------------------------------------------------

    def open_add_client_form(self):
        self.open_client_form()

    def open_edit_client_form(self, client):
        if not client.get('is_active', True):
            return
        self.open_client_form(client)

    def open_client_form(self, client=None):
        if client is not None and not client.get('is_active', True):
            return
        is_editing = client is not None

        employees = []

        if self.is_admin and not is_editing:
            session = SessionLocal()

            try:
                service = ClientService(session)
                database_employees = service.list_available_employees(
                    self.current_user
                )

                employees = [
                    SimpleNamespace(
                        id=employee.id,
                        full_name=employee.full_name,
                    )
                    for employee in database_employees
                ]

            finally:
                session.close()

        def save_client(data):
            session = SessionLocal()

            changes = {
                "company_name": data.get("name"),
                "internal_code": data.get("internal_code"),
                "ice": data.get("ice"),
                "if_number": data.get("if_number"),
                "cnss_number": data.get("cnss_number"),
                "rc_number": data.get("rc_number"),
                "rc_city": data.get("rc_city"),
                "patente": data.get("patente"),
                "address": data.get("address"),
                "contact_name": data.get("contact"),
                "email": data.get("email"),
                "phone_number": data.get("phone"),
            }

            try:
                service = ClientService(session)

                if is_editing:
                    updated_client = service.update_client(
                        self.current_user,
                        client["id"],
                        **changes,
                    )

                    if updated_client is None:
                        raise PermissionError(
                            "Client introuvable ou accès non autorisé."
                        )

                else:
                    if self.is_admin:
                        changes["responsible_user_id"] = (
                            data.get("responsible_user_id")
                        )

                    service.create_client(
                        self.current_user,
                        **changes,
                    )

                session.commit()

            except IntegrityError as error:
                session.rollback()

                raise ValueError(
                    "Le code interne ou l'ICE existe déjà. "
                    "Vérifiez ces deux champs."
                ) from error

            except Exception:
                session.rollback()
                raise

            finally:
                session.close()

            self._refresh_clients()
            return True

        dialog = ClientFormDialog(
            self,
            on_save=save_client,
            client=client,
            employees=employees,
            is_admin=self.is_admin,
        )

    # --------------------------------------------------
    # OUVRIR LES INFORMATIONS DU CLIENT
    # --------------------------------------------------

    def open_client_folder(self, client):
        ClientDetailDialog(self, self.current_user, client)


    # --------------------------------------------------
    # ARCHIVAGE
    # --------------------------------------------------

    def confirm_delete_client(self, client):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Archiver le client")
        dialog.geometry("430x240")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=colors.SURFACE)
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="Archiver ce client ?",
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
                f'Voulez-vous archiver « {client["name"]} » ?\n'
                "Ses données et ses documents seront conservés."
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

        self.archive_error = ctk.CTkLabel(
            dialog,
            text="",
            text_color=colors.ERROR,
            wraplength=370,
        )
        self.archive_error.grid(
            row=2,
            column=0,
            padx=20,
            pady=4,
        )

        actions = ctk.CTkFrame(
            dialog,
            fg_color="transparent",
        )
        actions.grid(
            row=3,
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

        def archive_client():
            session = SessionLocal()

            try:
                service = ClientService(session)

                archived = service.archive_client(
                    self.current_user,
                    client["id"],
                )

                if archived is None:
                    raise PermissionError(
                        "Client introuvable ou accès non autorisé."
                    )

                session.commit()

            except Exception as error:
                session.rollback()
                self.archive_error.configure(text=str(error))
                return

            finally:
                session.close()

            self._refresh_clients()
            dialog.destroy()

        ctk.CTkButton(
            actions,
            text="Confirmer l'archivage",
            fg_color=colors.ERROR,
            hover_color="#B8323B",
            command=archive_client,
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )

    def confirm_restore_client(self, client):
        dialog = ctk.CTkToplevel(self)
        dialog.title("R?activer le client")
        dialog.geometry("430x240")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=colors.SURFACE)
        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="R?activer ce client ?",
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
                f'Voulez-vous r?activer ? {client["name"]} ? ?\n'
                "Ses informations et son responsable seront conserv?s."
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

        error_label = ctk.CTkLabel(
            dialog,
            text="",
            text_color=colors.ERROR,
            wraplength=370,
        )
        error_label.grid(
            row=2,
            column=0,
            padx=20,
            pady=4,
        )

        actions = ctk.CTkFrame(
            dialog,
            fg_color="transparent",
        )
        actions.grid(
            row=3,
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

        def restore_client():
            session = SessionLocal()

            try:
                service = ClientService(session)
                restored = service.restore_client(
                    self.current_user,
                    client["id"],
                )

                if restored is None:
                    raise PermissionError(
                        "Client introuvable ou acc?s non autoris?."
                    )

                session.commit()

            except Exception as error:
                session.rollback()
                error_label.configure(text=str(error))
                return

            finally:
                session.close()

            self._refresh_clients()
            dialog.destroy()

        ctk.CTkButton(
            actions,
            text="Confirmer la r?activation",
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=restore_client,
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(6, 0),
        )
