import re
import customtkinter as ctk

from frontend.ui.styles import colors, typography


class ClientFormDialog(ctk.CTkToplevel):
    """Formulaire complet de création et de modification d'un client."""

    FIELDS = [
        ("name", "Nom de la société *", "Ex. Société Exemple SARL"),
        ("internal_code", "Code interne", "Code du client"),
        ("ice", "ICE", "Identifiant ICE"),
        ("if_number", "Identifiant fiscal (IF)", "Numéro IF"),
        ("cnss_number", "Numéro CNSS", "Numéro CNSS"),
        ("rc_number", "Numéro RC", "Numéro du registre de commerce"),
        ("rc_city", "Ville du RC", "Ville"),
        ("patente", "Patente", "Numéro de patente"),
        ("address", "Adresse", "Adresse de la société"),
        ("contact", "Nom du contact", "Nom et prénom"),
        ("email", "Email", "contact@entreprise.ma"),
        ("phone", "Téléphone", "0612345678"),
    ]

    def __init__(
        self,
        parent,
        on_save,
        client=None,
        employees=None,
        is_admin=False,
    ):
        super().__init__(parent)

        self.client = client or {}
        self.on_save = on_save
        self.is_editing = client is not None
        self.employees = employees or []
        self.is_admin = is_admin

        self.employee_options = {}

        for employee in self.employees:
            label = f"{employee.full_name} (ID: {employee.id})"
            self.employee_options[label] = employee.id

        self.title(
            "Modifier un client"
            if self.is_editing
            else "Ajouter un client"
        )
        screen_height = self.winfo_screenheight()
        screen_width = self.winfo_screenwidth()

        window_width = min(620, screen_width - 80)
        window_height = min(700, screen_height - 100)
        window_height = max(560, window_height)

        pos_x = max(0, (screen_width - window_width) // 2)
        pos_y = max(0, (screen_height - window_height) // 2)

        self.geometry(
            f"{window_width}x{window_height}+{pos_x}+{pos_y}"
        )
        self.minsize(520, 540)
        self.resizable(True, True)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.configure(fg_color=colors.SURFACE)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.entries = {}

        title = ctk.CTkLabel(
            self,
            text=(
                "Modifier les informations du client"
                if self.is_editing
                else "Nouveau client"
            ),
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=22,
                weight="bold",
            ),
            text_color=colors.TEXT_PRIMARY,
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=24,
            pady=(20, 12),
        )

        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.scroll_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=16,
            pady=4,
        )
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        current_row = 0

        for key, label, placeholder in self.FIELDS:
            ctk.CTkLabel(
                self.scroll_frame,
                text=label,
                text_color=colors.TEXT_SECONDARY,
                anchor="w",
            ).grid(
                row=current_row,
                column=0,
                sticky="ew",
                padx=10,
                pady=(9, 2),
            )

            current_row += 1

            entry = ctk.CTkEntry(
                self.scroll_frame,
                placeholder_text=placeholder,
                height=38,
            )
            entry.grid(
                row=current_row,
                column=0,
                sticky="ew",
                padx=10,
                pady=(2, 5),
            )

            self.entries[key] = entry

            value = self.client.get(key, "")
            if value is not None and str(value).strip():
                entry.insert(0, str(value))

            current_row += 1

        self.responsible_var = None

        if self.is_admin and not self.is_editing:
            ctk.CTkLabel(
                self.scroll_frame,
                text="Employé responsable *",
                text_color=colors.TEXT_SECONDARY,
                anchor="w",
            ).grid(
                row=current_row,
                column=0,
                sticky="ew",
                padx=10,
                pady=(12, 2),
            )

            current_row += 1

            options = (
                ["Choisir un employé"]
                + list(self.employee_options.keys())
            )

            self.responsible_var = ctk.StringVar(
                value="Choisir un employé"
            )

            self.employee_menu = ctk.CTkOptionMenu(
                self.scroll_frame,
                values=options,
                variable=self.responsible_var,
                height=38,
                fg_color=colors.PRIMARY,
                button_color=colors.PRIMARY_HOVER,
                button_hover_color=colors.PRIMARY_HOVER,
            )
            self.employee_menu.grid(
                row=current_row,
                column=0,
                sticky="ew",
                padx=10,
                pady=(2, 12),
            )

            current_row += 1

            if not self.employees:
                self.employee_menu.configure(state="disabled")
                ctk.CTkLabel(
                    self.scroll_frame,
                    text="Aucun employé actif disponible.",
                    text_color=colors.ERROR,
                ).grid(
                    row=current_row,
                    column=0,
                    sticky="w",
                    padx=10,
                    pady=4,
                )
                current_row += 1

        footer = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        footer.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=24,
            pady=(8, 18),
        )
        footer.grid_columnconfigure((0, 1), weight=1)

        self.message = ctk.CTkLabel(
            footer,
            text="",
            text_color=colors.ERROR,
            wraplength=540,
        )
        self.message.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )

        ctk.CTkButton(
            footer,
            text="Annuler",
            height=40,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            command=self.destroy,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 6),
        )

        ctk.CTkButton(
            footer,
            text="Enregistrer",
            height=40,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=self.save,
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(6, 0),
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
            valid_email = re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                data["email"],
            )

            if not valid_email:
                self.message.configure(
                    text="Veuillez saisir une adresse email valide."
                )
                return

        if self.responsible_var is not None:
            selected = self.responsible_var.get()

            if selected not in self.employee_options:
                self.message.configure(
                    text="Veuillez choisir un employé responsable."
                )
                return

            data["responsible_user_id"] = (
                self.employee_options[selected]
            )

        try:
            result = self.on_save(data)

            if result is not False:
                self.destroy()

        except Exception as error:
            self.message.configure(
                text=f"Erreur lors de l'enregistrement : {error}"
            )
