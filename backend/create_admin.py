
from getpass import getpass

from sqlalchemy.exc import IntegrityError

from backend.database.connection import SessionLocal
from backend.database.models.user import User, UserRole
from backend.services.auth_service import AuthService


def main():
    session = SessionLocal()

    try:
        # Prevent creating a second administrator.
        existing_admin = (
            session.query(User)
            .filter(User.role == UserRole.ADMIN)
            .first()
        )

        if existing_admin:
            print("Un compte Responsable existe déjà.")
            return

        print("\n=== Création du premier Responsable FIDOMEK ONE ===")

        full_name = input("Nom complet : ").strip()
        email = input("Adresse e-mail : ").strip().lower()

        if not full_name or not email or "@" not in email:
            print("Nom ou adresse e-mail invalide.")
            return

        existing_user = (
            session.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("Cette adresse e-mail est déjà utilisée.")
            return

        password = getpass("Mot de passe (8 caractères minimum) : ")
        confirmation = getpass("Confirmer le mot de passe : ")

        if len(password) < 8:
         print("Le mot de passe doit contenir au moins 8 caractères.")
         return

        if password != confirmation:
            print("Les mots de passe ne correspondent pas.")
            return

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=AuthService.hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )

        session.add(admin)
        session.commit()

        print("\nCompte Responsable créé avec succès.")
        print(f"Nom : {admin.full_name}")
        print(f"E-mail : {admin.email}")
        print(f"Rôle : {admin.role.value}")

    except IntegrityError:
        session.rollback()
        print("Erreur : cette adresse e-mail existe peut-être déjà.")

    except Exception:
        session.rollback()
        print("Une erreur est survenue pendant la création du compte.")
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
