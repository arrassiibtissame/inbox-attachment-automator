from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk

from backend.database.connection import SessionLocal
from backend.database.models.client import Client
from backend.database.models.user import UserRole
from backend.services.client_service import ClientService
from backend.services.client_document_service import ClientDocumentService
from backend.services.client_manual_document_service import ClientManualDocumentService
from backend.services.client_note_service import ClientNoteService
from backend.services.client_reminder_service import ClientReminderService
from backend.services.client_event_service import ClientEventService

from frontend.ui.components.document_preview_panel import DocumentPreviewPanel
from frontend.ui.styles import colors, typography


class ClientDetailDialog:
    CATEGORIES = [
        "Toutes",
        "Juridique",
        "Fiscalité",
        "Comptabilité",
        "Social",
        "Banque",
        "Non classés",
    ]

    STATUSES = ["Tous", "TO_REVIEW", "CLASSIFIED"]
    STATUS_LABELS = {
        "TO_REVIEW": "\u00c0 v\u00e9rifier",
        "CLASSIFIED": "Class\u00e9 automatiquement",
    }
    REMINDER_STATUSES = ["? faire", "En cours", "Termin?"]

    def __init__(self, parent, current_user, client_data):
        self.parent = parent
        self.current_user = current_user
        self.client_id = client_data["id"]
        self.client_name = client_data.get("name", "Client")
        self.page = 1
        self.page_size = 20
        self.total_pages = 1
        self.documents = []
        self.selected_document = None

        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Dossier client ? {self.client_name}")
        self.window.geometry("1180x780")
        self.window.minsize(950, 650)
        self.window.configure(fg_color=colors.BACKGROUND)
        self.window.transient(parent.winfo_toplevel())
        self.window.grab_set()

        self._build_header()
        self.tabs = ctk.CTkTabview(
            self.window,
            fg_color=colors.SURFACE,
            segmented_button_selected_color=colors.PRIMARY,
            segmented_button_selected_hover_color=colors.PRIMARY_HOVER,
        )
        self.tabs.pack(fill="both", expand=True, padx=22, pady=(0, 20))

        self.tabs.add("Informations")
        self.tabs.add("Documents")
        self.tabs.add("Historique")
        self.tabs.add("Notes et rappels")

        self._build_information_tab()
        self._build_documents_tab()
        self._build_history_tab()
        self._build_notes_tab()

        self.refresh_all()

    def _session(self, callback, commit=False):
        session = SessionLocal()
        try:
            result = callback(session)
            if commit:
                session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _client_data(self, session):
        service = ClientService(session)
        client = service.get_client(self.current_user, self.client_id)
        if client is None:
            raise PermissionError("Client introuvable ou acc?s non autoris?.")

        responsible = client.responsible_user
        return {
            "name": client.company_name,
            "internal_code": client.internal_code,
            "ice": client.ice,
            "if_number": client.if_number,
            "cnss_number": client.cnss_number,
            "rc_number": client.rc_number,
            "rc_city": client.rc_city,
            "patente": client.patente,
            "legal_form": client.legal_form,
            "business_sector": client.business_sector,
            "incorporation_date": client.incorporation_date,
            "tax_regime": client.tax_regime,
            "collaboration_start_date": client.collaboration_start_date,
            "phone_number": client.phone_number,
            "contact_name": client.contact_name,
            "email": client.email,
            "address": client.address,
            "responsible": responsible.full_name if responsible else "Non attribué",
            "created_at": client.created_at,
            "updated_at": client.updated_at,
            "is_active": client.is_active,
        }

    def _build_header(self):
        header = ctk.CTkFrame(self.window, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=self.client_name,
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header,
            text="Fermer",
            width=90,
            command=self.window.destroy,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=1, sticky="e")

    def _section_label(self, parent, text, row, column=0):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=row, column=column, sticky="w", padx=8, pady=(12, 5))

    def _build_information_tab(self):
        tab = self.tabs.tab("Informations")
        self.info_frame = ctk.CTkScrollableFrame(
            tab, fg_color="transparent"
        )
        self.info_frame.pack(fill="both", expand=True, padx=12, pady=12)
        self.info_frame.grid_columnconfigure((0, 1), weight=1)

    def _refresh_information(self):
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        try:
            data = self._session(self._client_data)
        except Exception as error:
            messagebox.showerror("Dossier client", str(error), parent=self.window)
            return

        groups = [
            ("Identification", [
                ("Code interne", "internal_code"),
                ("ICE", "ice"),
                ("Identifiant fiscal", "if_number"),
                ("CNSS", "cnss_number"),
                ("Patente", "patente"),
                ("Registre de commerce", "rc_number"),
                ("Ville du RC", "rc_city"),
            ]),
            ("Informations juridiques et fiscales", [
                ("Forme juridique", "legal_form"),
                ("Secteur d'activit?", "business_sector"),
                ("Date de cr?ation", "incorporation_date"),
                ("R?gime fiscal", "tax_regime"),
                ("D?but de collaboration", "collaboration_start_date"),
            ]),
            ("Coordonn?es", [
                ("Contact principal", "contact_name"),
                ("T?l?phone", "phone_number"),
                ("E-mail", "email"),
                ("Adresse", "address"),
            ]),
            ("Gestion du dossier", [
                ("Responsable", "responsible"),
                ("Statut", "is_active"),
                ("Créé le", "created_at"),
                ("Modifié le", "updated_at"),
            ]),
        ]

        row = 0
        for title, fields in groups:
            self._section_label(self.info_frame, title, row)
            row += 1
            for index, (label, key) in enumerate(fields):
                value = data.get(key)
                if value is None or value == "":
                    value = "Non renseign?"
                elif isinstance(value, datetime):
                    value = value.strftime("%d/%m/%Y %H:%M")
                elif hasattr(value, "strftime"):
                    value = value.strftime("%d/%m/%Y")
                elif key == "is_active":
                    value = "Actif" if value else "Archiv?"

                card = ctk.CTkFrame(
                    self.info_frame,
                    fg_color=colors.BACKGROUND,
                    corner_radius=9,
                )
                card.grid(
                    row=row + index // 2,
                    column=index % 2,
                    sticky="ew",
                    padx=7,
                    pady=5,
                )
                ctk.CTkLabel(
                    card,
                    text=label,
                    text_color=colors.TEXT_SECONDARY,
                    font=ctk.CTkFont(size=11),
                ).pack(anchor="w", padx=12, pady=(8, 2))
                ctk.CTkLabel(
                    card,
                    text=str(value),
                    text_color=colors.TEXT_PRIMARY,
                    font=ctk.CTkFont(size=13, weight="bold"),
                    wraplength=420,
                    justify="left",
                ).pack(anchor="w", padx=12, pady=(0, 9))
            row += (len(fields) + 1) // 2

    DOCUMENT_CATEGORIES = [
        "Juridique",
        "Fiscalité",
        "Comptabilité",
        "Social",
        "Banque",
        "Non classés",
    ]

    def _build_documents_tab(self):
        tab = self.tabs.tab("Documents")
        tab.grid_columnconfigure(0, weight=3)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(1, weight=1)

        filters = ctk.CTkFrame(tab, fg_color="transparent")
        filters.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=8)
        filters.grid_columnconfigure(0, weight=1)

        self.document_search = ctk.CTkEntry(
            filters, placeholder_text="Rechercher un fichier..."
        )
        self.document_search.grid(row=0, column=0, sticky="ew", padx=4)
        self.document_search.bind(
            "<Return>", lambda event: self._refresh_documents(reset=True)
        )

        self.category_filter = ctk.CTkOptionMenu(
            filters,
            values=self.CATEGORIES,
            command=lambda value: self._refresh_documents(reset=True),
        )
        self.category_filter.set("Toutes")
        self.category_filter.grid(row=0, column=1, padx=4)

        self.status_filter = ctk.CTkOptionMenu(
            filters,
            values=self.STATUSES,
            command=lambda value: self._refresh_documents(reset=True),
        )
        self.status_filter.set("Tous")
        self.status_filter.grid(row=0, column=2, padx=4)

        ctk.CTkButton(
            filters,
            text="Rechercher",
            width=95,
            command=lambda: self._refresh_documents(reset=True),
        ).grid(row=0, column=3, padx=4)

        ctk.CTkButton(
            filters,
            text="+ Ajouter un document",
            width=155,
            command=self._add_manual_document,
        ).grid(row=0, column=4, padx=4)

        self.document_list = ctk.CTkScrollableFrame(
            tab, fg_color="transparent"
        )
        self.document_list.grid(
            row=1, column=0, sticky="nsew", padx=(8, 5), pady=5
        )

        self.preview = DocumentPreviewPanel(tab)
        self.preview.grid(
            row=1, column=1, sticky="nsew", padx=(5, 8), pady=5
        )

        footer = ctk.CTkFrame(tab, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=8, pady=8)
        self.documents_page_label = ctk.CTkLabel(
            footer, text="Page 1 / 1"
        )
        self.documents_page_label.pack(side="left")
        ctk.CTkButton(
            footer, text="Pr?c?dent", width=90,
            command=self._previous_documents_page
        ).pack(side="right", padx=3)
        ctk.CTkButton(
            footer, text="Suivant", width=90,
            command=self._next_documents_page
        ).pack(side="right", padx=3)

    def _refresh_documents(self, reset=False):
        if reset:
            self.page = 1

        search = self.document_search.get().strip()
        category = self.category_filter.get()
        status = self.status_filter.get()

        def load(session):
            service = ClientDocumentService(session)
            return service.list_client_documents(
                self.current_user,
                self.client_id,
                search=search or None,
                category=None if category == "Toutes" else category,
                status=None if status == "Tous" else status,
                page=self.page,
                page_size=self.page_size,
            )

        try:
            result = self._session(load)
        except Exception as error:
            messagebox.showerror("Documents", str(error), parent=self.window)
            return

        self.documents = result["items"]
        self.total_pages = max(1, result["total_pages"])

        for widget in self.document_list.winfo_children():
            widget.destroy()

        if not self.documents:
            ctk.CTkLabel(
                self.document_list,
                text="Aucun document trouv?.",
                text_color=colors.TEXT_SECONDARY,
            ).pack(padx=15, pady=25)
        else:
            for document in self.documents:
                card = ctk.CTkFrame(
                    self.document_list,
                    fg_color=colors.SURFACE,
                    border_width=1,
                    border_color=colors.BORDER,
                    corner_radius=9,
                )
                card.pack(fill="x", padx=4, pady=5)

                name = ctk.CTkLabel(
                    card,
                    text=document["name"],
                    text_color=colors.TEXT_PRIMARY,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    wraplength=380,
                    justify="left",
                )
                name.pack(anchor="w", padx=10, pady=(8, 2))

                date_value = document.get("date")
                date_text = (
                    date_value.strftime("%d/%m/%Y %H:%M")
                    if date_value else "Date inconnue"
                )
                category_text = document.get("category") or "Non class\u00e9s"
                status_value = str(document.get("status", "TO_REVIEW"))
                status_text = self.STATUS_LABELS.get(status_value, status_value)
                ctk.CTkLabel(
                    card,
                    text=f"{category_text} \u2022 {date_text} \u2022 {status_text}",
                    text_color=colors.TEXT_SECONDARY,
                    font=ctk.CTkFont(size=10),
                ).pack(anchor="w", padx=10, pady=(0, 5))

                actions = ctk.CTkFrame(card, fg_color="transparent")
                actions.pack(anchor="e", padx=8, pady=(0, 8))

                ctk.CTkButton(
                    actions,
                    text="Modifier la cat?gorie",
                    width=135,
                    height=28,
                    command=lambda item=document: self._edit_document_category(item),
                ).pack(side="left", padx=3)

                ctk.CTkButton(
                    actions,
                    text="Afficher l'aper?u",
                    height=28,
                    command=lambda item=document: self._show_document(item),
                ).pack(side="left", padx=3)

        self.documents_page_label.configure(
            text=f"Page {self.page} / {self.total_pages} ? {result['total']} document(s)"
        )


    def _choose_document_category(self, initial="Non classés"):
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Cat?gorie du document")
        dialog.geometry("380x190")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        result = {"value": None}

        ctk.CTkLabel(
            dialog,
            text="S?lectionner une cat?gorie :",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(22, 8))

        category_menu = ctk.CTkOptionMenu(
            dialog,
            values=self.DOCUMENT_CATEGORIES,
            width=320,
        )
        category_menu.pack(padx=20, pady=8)
        category_menu.set(
            initial if initial in self.DOCUMENT_CATEGORIES else "Non classés"
        )

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=15)

        def confirm():
            result["value"] = category_menu.get()
            dialog.destroy()

        ctk.CTkButton(
            buttons,
            text="Annuler",
            command=dialog.destroy,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            buttons,
            text="Valider",
            command=confirm,
        ).pack(side="right", padx=4)

        dialog.wait_window()
        return result["value"]

    def _add_manual_document(self):
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="Choisir un document ? ajouter",
            filetypes=[
                (
                    "Documents autoris?s",
                    "*.pdf *.png *.jpg *.jpeg *.webp *.doc *.docx *.xls *.xlsx *.csv",
                ),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not file_path:
            return

        category = self._choose_document_category()
        if category is None:
            return

        try:
            selected_path = Path(file_path)
            content = selected_path.read_bytes()

            def save(session):
                service = ClientManualDocumentService(session)
                return service.add_manual_document(
                    self.current_user,
                    self.client_id,
                    filename=selected_path.name,
                    content=content,
                    category=category,
                )

            self._session(save, commit=True)

        except Exception as error:
            messagebox.showerror(
                "Ajout du document",
                str(error),
                parent=self.window,
            )
            return

        messagebox.showinfo(
            "Document ajouté",
            "Le document a ?t? ajout? au dossier client.",
            parent=self.window,
        )
        self._refresh_documents(reset=True)
        self._refresh_history()

    def _edit_document_category(self, item):
        current_category = item.get("category") or "Non classés"
        category = self._choose_document_category(current_category)

        if category is None:
            return

        try:
            def update(session):
                service = ClientManualDocumentService(session)
                return service.update_document_category(
                    self.current_user,
                    self.client_id,
                    item["document_id"],
                    category,
                )

            self._session(update, commit=True)

        except Exception as error:
            messagebox.showerror(
                "Modification de la cat?gorie",
                str(error),
                parent=self.window,
            )
            return

        self._refresh_documents()
        self._refresh_history()

    def _show_document(self, item):
        size = item.get("size_bytes") or 0
        if size >= 1024 * 1024:
            size_text = f"{size / (1024 * 1024):.2f} Mo"
        elif size >= 1024:
            size_text = f"{size / 1024:.1f} Ko"
        else:
            size_text = f"{size} octets"

        date_value = item.get("date")
        preview_data = {
            "path": item.get("path"),
            "name": item.get("name"),
            "client": item.get("client"),
            "type": item.get("type") or item.get("extension") or "Document",
            "date": (
                date_value.strftime("%d/%m/%Y %H:%M")
                if date_value else "Non renseign?e"
            ),
            "size": size_text,
            "status": self.STATUS_LABELS.get(
                str(item.get("status", "TO_REVIEW")),
                str(item.get("status", "TO_REVIEW")),
            ),
        }
        self.preview.show_document(preview_data)

    def _previous_documents_page(self):
        if self.page > 1:
            self.page -= 1
            self._refresh_documents()

    def _next_documents_page(self):
        if self.page < self.total_pages:
            self.page += 1
            self._refresh_documents()

    def _build_history_tab(self):
        tab = self.tabs.tab("Historique")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            tab,
            text="Activit? du dossier client",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=12, pady=12)

        self.history_list = ctk.CTkScrollableFrame(
            tab, fg_color="transparent"
        )
        self.history_list.grid(
            row=1, column=0, sticky="nsew", padx=10, pady=5
        )

    def _refresh_history(self):
        def load(session):
            service = ClientEventService(session)
            events = service.list_events(
                self.current_user, self.client_id, limit=300
            )
            return [
                {
                    "type": event.event_type,
                    "date": event.created_at,
                    "actor": event.actor.full_name if event.actor else "Système",
                    "old": event.old_values,
                    "new": event.new_values,
                    "metadata": event.event_metadata,
                }
                for event in events
            ]

        try:
            events = self._session(load)
        except Exception as error:
            messagebox.showerror("Historique", str(error), parent=self.window)
            return

        for widget in self.history_list.winfo_children():
            widget.destroy()

        if not events:
            ctk.CTkLabel(
                self.history_list,
                text="Aucune activit? enregistr?e pour ce client.",
                text_color=colors.TEXT_SECONDARY,
            ).pack(pady=25)
            return

        labels = {
            "NOTE_CREATED": "Note ajoutée",
            "NOTE_UPDATED": "Note modifiée",
            "NOTE_ARCHIVED": "Note archivée",
            "REMINDER_CREATED": "Rappel créé",
            "REMINDER_UPDATED": "Rappel modifié",
            "REMINDER_ARCHIVED": "Rappel archivé",
            "DOCUMENT_MANUALLY_ADDED": "Document ajouté",
            "DOCUMENT_CATEGORY_CHANGED": "Catégorie du document modifiée",
        }

        for event in events:
            card = ctk.CTkFrame(
                self.history_list,
                fg_color=colors.SURFACE,
                border_width=1,
                border_color=colors.BORDER,
                corner_radius=9,
            )
            card.pack(fill="x", padx=5, pady=5)

            date_value = event["date"]
            date_text = (
                date_value.strftime("%d/%m/%Y ? %H:%M")
                if date_value else "Date inconnue"
            )
            title = labels.get(
                event["type"],
                event["type"].replace("_", " ").capitalize(),
            )

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=colors.TEXT_PRIMARY,
            ).pack(anchor="w", padx=12, pady=(9, 2))
            ctk.CTkLabel(
                card,
                text=f"{date_text}  — Par {event['actor']}",
                text_color=colors.TEXT_SECONDARY,
                font=ctk.CTkFont(size=11),
            ).pack(anchor="w", padx=12, pady=(0, 9))

    def _build_notes_tab(self):
        tab = self.tabs.tab("Notes et rappels")
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(1, weight=1)

        left = ctk.CTkFrame(tab, fg_color="transparent")
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=8, pady=8)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(tab, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=8, pady=8)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left, text="Notes priv?es",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", pady=5)

        ctk.CTkButton(
            left, text="+ Ajouter une note",
            command=self._create_note,
        ).grid(row=0, column=1, padx=4)

        self.notes_list = ctk.CTkScrollableFrame(
            left, fg_color="transparent"
        )
        self.notes_list.grid(row=1, column=0, columnspan=2, sticky="nsew")

        ctk.CTkLabel(
            right, text="Rappels",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", pady=5)

        ctk.CTkButton(
            right, text="+ Ajouter un rappel",
            command=self._create_reminder,
        ).grid(row=0, column=1, padx=4)

        self.reminders_list = ctk.CTkScrollableFrame(
            right, fg_color="transparent"
        )
        self.reminders_list.grid(row=1, column=0, columnspan=2, sticky="nsew")

    def _refresh_notes(self):
        def load(session):
            notes = ClientNoteService(session).list_notes(
                self.current_user, self.client_id
            )
            return [
                {
                    "id": note.id,
                    "content": note.content,
                    "author_id": note.author_user_id,
                    "author": note.author.full_name,
                    "created": note.created_at,
                    "updated": note.updated_at,
                }
                for note in notes
            ]

        try:
            notes = self._session(load)
        except Exception as error:
            messagebox.showerror("Notes", str(error), parent=self.window)
            return

        for widget in self.notes_list.winfo_children():
            widget.destroy()

        if not notes:
            ctk.CTkLabel(
                self.notes_list, text="Aucune note.",
                text_color=colors.TEXT_SECONDARY,
            ).pack(pady=20)

        for note in notes:
            card = ctk.CTkFrame(
                self.notes_list, fg_color=colors.SURFACE,
                border_width=1, border_color=colors.BORDER,
                corner_radius=9,
            )
            card.pack(fill="x", padx=4, pady=5)

            ctk.CTkLabel(
                card, text=note["content"],
                text_color=colors.TEXT_PRIMARY,
                wraplength=390, justify="left",
            ).pack(anchor="w", padx=10, pady=(9, 4))

            created = note["created"].strftime("%d/%m/%Y %H:%M")
            ctk.CTkLabel(
                card, text=f"{note['author']} — {created}",
                text_color=colors.TEXT_SECONDARY,
                font=ctk.CTkFont(size=10),
            ).pack(anchor="w", padx=10, pady=(0, 5))

            if note["author_id"] == self.current_user.id:
                actions = ctk.CTkFrame(card, fg_color="transparent")
                actions.pack(anchor="e", padx=5, pady=(0, 6))
                ctk.CTkButton(
                    actions, text="Modifier", width=75, height=26,
                    command=lambda item=note: self._edit_note(item),
                ).pack(side="left", padx=3)
                ctk.CTkButton(
                    actions, text="Archiver", width=75, height=26,
                    fg_color=colors.SURFACE_ALT,
                    text_color=colors.TEXT_PRIMARY,
                    command=lambda item=note: self._archive_note(item),
                ).pack(side="left", padx=3)

    def _refresh_reminders(self):
        def load(session):
            reminders = ClientReminderService(session).list_reminders(
                self.current_user, self.client_id
            )
            return [
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "due_at": item.due_at,
                    "status": item.status,
                    "author_id": item.author_user_id,
                    "author": item.author.full_name,
                }
                for item in reminders
            ]

        try:
            reminders = self._session(load)
        except Exception as error:
            messagebox.showerror("Rappels", str(error), parent=self.window)
            return

        for widget in self.reminders_list.winfo_children():
            widget.destroy()

        if not reminders:
            ctk.CTkLabel(
                self.reminders_list, text="Aucun rappel.",
                text_color=colors.TEXT_SECONDARY,
            ).pack(pady=20)

        for item in reminders:
            card = ctk.CTkFrame(
                self.reminders_list, fg_color=colors.SURFACE,
                border_width=1, border_color=colors.BORDER,
                corner_radius=9,
            )
            card.pack(fill="x", padx=4, pady=5)

            ctk.CTkLabel(
                card, text=item["title"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=colors.TEXT_PRIMARY,
            ).pack(anchor="w", padx=10, pady=(8, 2))

            due = item["due_at"].strftime("%d/%m/%Y %H:%M")
            ctk.CTkLabel(
                card,
                text=f"{due} — {item['status']} — {item['author']}",
                text_color=colors.TEXT_SECONDARY,
                font=ctk.CTkFont(size=10),
            ).pack(anchor="w", padx=10, pady=2)

            if item["description"]:
                ctk.CTkLabel(
                    card, text=item["description"],
                    text_color=colors.TEXT_SECONDARY,
                    wraplength=390, justify="left",
                ).pack(anchor="w", padx=10, pady=3)

            if item["author_id"] == self.current_user.id:
                actions = ctk.CTkFrame(card, fg_color="transparent")
                actions.pack(anchor="e", padx=5, pady=(3, 6))
                ctk.CTkButton(
                    actions, text="Modifier", width=75, height=26,
                    command=lambda value=item: self._edit_reminder(value),
                ).pack(side="left", padx=3)
                ctk.CTkButton(
                    actions, text="Archiver", width=75, height=26,
                    fg_color=colors.SURFACE_ALT,
                    text_color=colors.TEXT_PRIMARY,
                    command=lambda value=item: self._archive_reminder(value),
                ).pack(side="left", padx=3)

    def _text_dialog(self, title, initial=""):
        dialog = ctk.CTkToplevel(self.window)
        dialog.title(title)
        dialog.geometry("480x330")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        textbox = ctk.CTkTextbox(dialog, height=210)
        textbox.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        textbox.insert("1.0", initial)
        result = {"value": None}

        def save():
            value = textbox.get("1.0", "end").strip()
            if not value:
                messagebox.showwarning(
                    "Champ obligatoire", "Le contenu est obligatoire.",
                    parent=dialog,
                )
                return
            result["value"] = value
            dialog.destroy()

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.grid(row=1, column=0, sticky="e", padx=15, pady=10)
        ctk.CTkButton(
            buttons, text="Annuler",
            fg_color=colors.SURFACE_ALT,
            text_color=colors.TEXT_PRIMARY,
            command=dialog.destroy,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            buttons, text="Enregistrer", command=save,
        ).pack(side="left", padx=5)

        dialog.wait_window()
        return result["value"]

    def _create_note(self):
        content = self._text_dialog("Nouvelle note")
        if content is None:
            return
        try:
            self._session(
                lambda session: ClientNoteService(session).create_note(
                    self.current_user, self.client_id, content
                ),
                commit=True,
            )
            self._refresh_notes()
            self._refresh_history()
        except Exception as error:
            messagebox.showerror("Note", str(error), parent=self.window)

    def _edit_note(self, note):
        content = self._text_dialog("Modifier la note", note["content"])
        if content is None:
            return
        try:
            self._session(
                lambda session: ClientNoteService(session).update_note(
                    self.current_user, self.client_id, note["id"], content
                ),
                commit=True,
            )
            self._refresh_notes()
            self._refresh_history()
        except Exception as error:
            messagebox.showerror("Note", str(error), parent=self.window)

    def _archive_note(self, note):
        if not messagebox.askyesno(
            "Archiver la note", "Voulez-vous archiver cette note ?",
            parent=self.window,
        ):
            return
        try:
            self._session(
                lambda session: ClientNoteService(session).archive_note(
                    self.current_user, self.client_id, note["id"]
                ),
                commit=True,
            )
            self._refresh_notes()
            self._refresh_history()
        except Exception as error:
            messagebox.showerror("Note", str(error), parent=self.window)

    def _reminder_dialog(self, initial=None):
        initial = initial or {}
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Rappel")
        dialog.geometry("480x500")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)

        def field(label, value="", row=0):
            ctk.CTkLabel(
                dialog, text=label, text_color=colors.TEXT_PRIMARY
            ).grid(row=row, column=0, sticky="w", padx=18, pady=(9, 2))
            entry = ctk.CTkEntry(dialog)
            entry.grid(row=row + 1, column=0, sticky="ew", padx=18)
            entry.insert(0, value)
            return entry

        title_entry = field("Titre", initial.get("title", ""), 0)
        due_value = initial.get("due_at")
        due_text = (
            due_value.strftime("%Y-%m-%d %H:%M")
            if due_value else datetime.now().strftime("%Y-%m-%d 17:00")
        )
        due_entry = field("Échéance (AAAA-MM-JJ HH:MM)", due_text, 2)

        ctk.CTkLabel(
            dialog, text="Description", text_color=colors.TEXT_PRIMARY
        ).grid(row=4, column=0, sticky="w", padx=18, pady=(9, 2))
        description = ctk.CTkTextbox(dialog, height=100)
        description.grid(row=5, column=0, sticky="ew", padx=18)
        description.insert("1.0", initial.get("description") or "")

        ctk.CTkLabel(
            dialog, text="Statut", text_color=colors.TEXT_PRIMARY
        ).grid(row=6, column=0, sticky="w", padx=18, pady=(9, 2))
        status = ctk.CTkOptionMenu(
            dialog, values=self.REMINDER_STATUSES
        )
        status.set(initial.get("status", "? faire"))
        status.grid(row=7, column=0, sticky="ew", padx=18)

        result = {"value": None}

        def save():
            title = title_entry.get().strip()
            try:
                due_at = datetime.strptime(
                    due_entry.get().strip(), "%Y-%m-%d %H:%M"
                )
            except ValueError:
                messagebox.showwarning(
                    "Date invalide",
                    "Utilisez le format AAAA-MM-JJ HH:MM.",
                    parent=dialog,
                )
                return

            if not title:
                messagebox.showwarning(
                    "Titre obligatoire", "Saisissez un titre.",
                    parent=dialog,
                )
                return

            result["value"] = {
                "title": title,
                "due_at": due_at,
                "description": description.get("1.0", "end").strip() or None,
                "status": status.get(),
            }
            dialog.destroy()

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.grid(row=8, column=0, sticky="e", padx=18, pady=15)
        ctk.CTkButton(
            buttons, text="Annuler",
            fg_color=colors.SURFACE_ALT,
            text_color=colors.TEXT_PRIMARY,
            command=dialog.destroy,
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            buttons, text="Enregistrer", command=save,
        ).pack(side="left", padx=5)

        dialog.wait_window()
        return result["value"]

    def _create_reminder(self):
        values = self._reminder_dialog()
        if values is None:
            return
        try:
            self._session(
                lambda session: ClientReminderService(session).create_reminder(
                    self.current_user, self.client_id, **values
                ),
                commit=True,
            )
            self._refresh_reminders()
            self._refresh_history()
        except Exception as error:
            messagebox.showerror("Rappel", str(error), parent=self.window)

    def _edit_reminder(self, item):
        values = self._reminder_dialog(item)
        if values is None:
            return
        try:
            self._session(
                lambda session: ClientReminderService(session).update_reminder(
                    self.current_user, self.client_id, item["id"], **values
                ),
                commit=True,
            )
            self._refresh_reminders()
            self._refresh_history()
        except Exception as error:
            messagebox.showerror("Rappel", str(error), parent=self.window)

    def _archive_reminder(self, item):
        if not messagebox.askyesno(
            "Archiver le rappel", "Voulez-vous archiver ce rappel ?",
            parent=self.window,
        ):
            return
        try:
            self._session(
                lambda session: ClientReminderService(session).archive_reminder(
                    self.current_user, self.client_id, item["id"]
                ),
                commit=True,
            )
            self._refresh_reminders()
            self._refresh_history()
        except Exception as error:
            messagebox.showerror("Rappel", str(error), parent=self.window)

    def refresh_all(self):
        self._refresh_information()
        self._refresh_documents(reset=True)
        self._refresh_history()
        self._refresh_notes()
        self._refresh_reminders()
