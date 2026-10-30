
import re
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientFormDialog(ctk.CTkToplevel):
    """Reusable dialog for adding or editing a client."""

    def __init__(self, parent, on_save, client=None):
        super().__init__(parent)

        self.client = client
        self.on_save = on_save
        self.is_editing = client is not None

        self.title(
            "Modifier un client" if self.is_editing else "Ajouter un client"
        )
        self.geometry("460x680")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.configure(fg_color=colors.SURFACE)
        self.grid_columnconfigure(0, weight=1)

        self.entries = {}

        title = "Modifier le client" if self.is_editing else "Nouveau client"

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=22,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(22, 16))

        fields = [
            ("name", "Nom de la société *", "Ex. Société Exemple SARL"),
            ("tax_id", "Identifiant fiscal", "Identifiant fiscal"),
            ("contact", "Nom du contact", "Nom et prénom"),
            ("email", "Email", "contact@entreprise.ma"),
            ("phone", "Numéro de téléphone", "Ex. 0612345678"),
        ]

        for index, (key, label, placeholder) in enumerate(fields):
            label_row = index * 2 + 1
            entry_row = label_row + 1

            ctk.CTkLabel(
                self,
                text=label,
                text_color=colors.TEXT_SECONDARY,
            ).grid(
                row=label_row,
                column=0,
                sticky="w",
                padx=24,
            )

            entry = ctk.CTkEntry(
                self,
                placeholder_text=placeholder,
                height=38,
            )
            entry.grid(
                row=entry_row,
                column=0,
                sticky="ew",
                padx=24,
                pady=(5, 12),
            )

            self.entries[key] = entry

            if self.is_editing:
                value = self.client.get(key, "")
                if value and value not in (
                    "Contact non renseigné",
                    "Email non renseigné",
                    "Téléphone non renseigné",
                ):
                    entry.insert(0, value)

        self.message = ctk.CTkLabel(
            self,
            text="",
            text_color=colors.ERROR,
            wraplength=400,
        )
        self.message.grid(row=11, column=0, padx=24, pady=(0, 4))

        ctk.CTkButton(
            self,
            text="Enregistrer les modifications" if self.is_editing
            else "Enregistrer le client",
            height=42,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=self.save,
        ).grid(
            row=12,
            column=0,
            sticky="ew",
            padx=24,
            pady=(8, 20),
        )

        self.entries["name"].focus()

    def save(self):
        data = {
            key: entry.get().strip()
            for key, entry in self.entries.items()
        }

        if not data["name"]:
            self.message.configure(
                text="Le nom de la société est obligatoire."
            )
            return

        if data["email"]:
            if not re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                data["email"],
            ):
                self.message.configure(
                    text="Veuillez saisir une adresse email valide."
                )
                return

        data["contact"] = data["contact"] or "Contact non renseigné"
        data["email"] = data["email"] or "Email non renseigné"
        data["phone"] = data["phone"] or "Téléphone non renseigné"

        self.on_save(data)
