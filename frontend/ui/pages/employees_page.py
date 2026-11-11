
import customtkinter as ctk
from tkinter import messagebox

from frontend.ui.components.page_header import PageHeader
from frontend.ui.styles import colors, typography
from backend.database.connection import SessionLocal
from backend.database.models.user import UserRole
from backend.services.employee_service import EmployeeService


class EmployeesPage(ctk.CTkFrame):
    """Page de gestion des employés réservée à l'administrateur."""

    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color="transparent")

        self.current_user = current_user
        self.employees = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = PageHeader(
            self,
            title="Gestion des employés",
            subtitle="Gérez les comptes et les informations de vos collaborateurs.",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=32,
            pady=(30, 20),
        )

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=32,
            pady=(0, 18),
        )
        toolbar.grid_columnconfigure(0, weight=1)

        self.count_label = ctk.CTkLabel(
            toolbar,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=colors.TEXT_SECONDARY,
        )
        self.count_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            toolbar,
            text="+ Ajouter un employé",
            height=42,
            corner_radius=10,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            font=ctk.CTkFont(
                family=typography.FONT_FAMILY,
                size=typography.BUTTON_SIZE,
                weight="bold",
            ),
            command=self.open_add_employee_form,
        ).grid(row=0, column=1)

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
        self.content.grid_columnconfigure(0, weight=1)

        self.load_employees()

    def load_employees(self):
        """Charger les employés depuis la base de données."""

        session = SessionLocal()

        try:
            service = EmployeeService(session)
            self.employees = service.list_employees(self.current_user)
        except Exception as error:
            messagebox.showerror(
                "Erreur",
                f"Impossible de charger les employés :\n{error}",
                parent=self,
            )
            self.employees = []
        finally:
            session.close()

        self.render_employees()

    def render_employees(self):
        """Afficher les cartes des employés."""

        for widget in self.content.winfo_children():
            widget.destroy()

        total = len(self.employees)
        active = sum(1 for employee in self.employees if employee.is_active)

        self.count_label.configure(
            text=f"{total} employé(s) · {active} actif(s)"
        )

        if not self.employees:
            ctk.CTkLabel(
                self.content,
                text="Aucun employé enregistré.",
                font=ctk.CTkFont(size=14),
                text_color=colors.TEXT_SECONDARY,
            ).grid(row=0, column=0, pady=32)
            return

        for row, employee in enumerate(self.employees):
            self.render_employee_card(employee, row)

    def render_employee_card(self, employee, row):
        """Créer une carte pour un employé."""

        card = ctk.CTkFrame(
            self.content,
            fg_color=colors.SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=colors.BORDER,
        )
        card.grid(
            row=row,
            column=0,
            sticky="ew",
            pady=(0, 12),
        )
        card.grid_columnconfigure(1, weight=1)

        avatar_text = (
            employee.full_name.strip()[:1].upper()
            if employee.full_name.strip()
            else "?"
        )

        avatar = ctk.CTkLabel(
            card,
            text=avatar_text,
            width=44,
            height=44,
            corner_radius=22,
            fg_color=colors.PRIMARY,
            text_color="white",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        avatar.grid(row=0, column=0, padx=16, pady=14)

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w", pady=12)

        display_name = (
            f"{employee.civility} {employee.full_name}"
            if employee.civility
            else employee.full_name
        )

        ctk.CTkLabel(
            info,
            text=display_name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=employee.email,
            font=ctk.CTkFont(size=12),
            text_color=colors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(4, 0))

        status = "Actif" if employee.is_active else "Inactif"
        status_color = (
            colors.SUCCESS if employee.is_active else colors.TEXT_SECONDARY
        )

        ctk.CTkLabel(
            card,
            text=status,
            text_color=status_color,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=2, padx=16)

        ctk.CTkButton(
            card,
            text="Modifier",
            width=90,
            height=34,
            fg_color=colors.SURFACE_ALT,
            hover_color=colors.BORDER,
            text_color=colors.TEXT_PRIMARY,
            command=lambda item=employee: self.open_edit_employee_form(item),
        ).grid(row=0, column=3, padx=(0, 8))

        ctk.CTkButton(
            card,
            text="Désactiver" if employee.is_active else "Réactiver",
            width=100,
            height=34,
            fg_color=colors.ERROR if employee.is_active else colors.SUCCESS,
            hover_color=(
                colors.ERROR_LIGHT if employee.is_active
                else colors.SUCCESS_LIGHT
            ),
            text_color="white",
            command=lambda item=employee: self.toggle_employee_status(item),
        ).grid(row=0, column=4, padx=(0, 16))

    def toggle_employee_status(self, employee):
        """Activer ou désactiver un compte après confirmation."""

        if employee.is_active:
            confirmed = messagebox.askyesno(
                "Confirmer la désactivation",
                (
                    f"Voulez-vous désactiver le compte de "
                    f"{employee.full_name} ?\\n\\n"
                    "L'employé ne pourra plus se connecter. "
                    "Son portefeuille client sera conserv?."
                ),
                parent=self,
            )
            if not confirmed:
                return

        session = SessionLocal()

        try:
            service = EmployeeService(session)
            service.set_employee_active(
                self.current_user,
                employee.id,
                not employee.is_active,
            )
            session.commit()

        except (ValueError, PermissionError) as error:
            session.rollback()
            messagebox.showerror(
                "Opération impossible",
                str(error),
                parent=self,
            )
            return

        except Exception as error:
            session.rollback()
            messagebox.showerror(
                "Erreur",
                f"Impossible de modifier le compte :\\n{error}",
                parent=self,
            )
            return

        finally:
            session.close()

        self.load_employees()

    def open_add_employee_form(self):
        """Ouvrir le formulaire de création."""

        dialog = ctk.CTkToplevel(self)
        dialog.title("Ajouter un employé")
        dialog.geometry("430x510")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=colors.SURFACE)

        self.build_employee_form(dialog)

    def open_edit_employee_form(self, employee):
        """Ouvrir le formulaire de modification."""

        dialog = ctk.CTkToplevel(self)
        dialog.title("Modifier un employé")
        dialog.geometry("430x430")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.configure(fg_color=colors.SURFACE)

        self.build_employee_form(dialog, employee)

    def build_employee_form(self, dialog, employee=None):
        """Construire le formulaire de création ou modification."""

        editing = employee is not None

        dialog.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            dialog,
            text="Modifier l'employé" if editing else "Nouvel employé",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=colors.TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=(24, 16))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=24)

        def add_field(label, value="", show=None):
            ctk.CTkLabel(
                form,
                text=label,
                text_color=colors.TEXT_SECONDARY,
            ).pack(anchor="w", pady=(8, 4))

            field = ctk.CTkEntry(
                form,
                height=38,
                show=show if show else "",
            )
            field.pack(fill="x")

            if value:
                field.insert(0, value)

            return field

        ctk.CTkLabel(
            form,
            text="Civilité",
            text_color=colors.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(4, 4))

        civility = ctk.CTkOptionMenu(
            form,
            values=["Monsieur", "Madame"],
            height=38,
            fg_color=colors.PRIMARY,
            button_color=colors.PRIMARY_HOVER,
        )
        civility.pack(fill="x")

        if editing and employee.civility:
            civility.set(employee.civility)
        else:
            civility.set("Monsieur")

        name_field = add_field(
            "Nom complet",
            employee.full_name if editing else "",
        )

        email_field = add_field(
            "Adresse e-mail",
            employee.email if editing else "",
        )

        password_field = None

        if not editing:
            password_field = add_field(
                "Mot de passe initial",
                show="*",
            )

        error_label = ctk.CTkLabel(
            dialog,
            text="",
            text_color=colors.ERROR,
            wraplength=370,
        )
        error_label.pack(padx=24, pady=(8, 0))

        def save():
            session = SessionLocal()

            try:
                service = EmployeeService(session)

                if editing:
                    service.update_employee(
                        self.current_user,
                        employee.id,
                        full_name=name_field.get(),
                        civility=civility.get(),
                        email=email_field.get(),
                    )
                else:
                    service.create_employee(
                        self.current_user,
                        full_name=name_field.get(),
                        civility=civility.get(),
                        email=email_field.get(),
                        password=password_field.get(),
                    )

                session.commit()

            except (ValueError, PermissionError) as error:
                session.rollback()
                error_label.configure(text=str(error))
                return

            except Exception as error:
                session.rollback()
                error_label.configure(
                    text=f"Une erreur est survenue : {error}"
                )
                return

            finally:
                session.close()

            dialog.destroy()
            self.load_employees()

        ctk.CTkButton(
            dialog,
            text="Enregistrer",
            height=42,
            fg_color=colors.PRIMARY,
            hover_color=colors.PRIMARY_HOVER,
            command=save,
        ).pack(fill="x", padx=24, pady=(12, 22))
