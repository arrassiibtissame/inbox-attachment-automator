from sqlalchemy.orm import Session

from backend.database.models.document import DocumentStatus
from backend.database.models.document_classification import (
    ClassificationDecision,
)
from backend.database.models.user import User
from backend.database.repositories.document_classification_repository import (
    DocumentClassificationRepository,
)
from backend.database.repositories.document_event_repository import (
    DocumentEventRepository,
)
from backend.database.repositories.document_repository import (
    DocumentRepository,
)
from backend.services.client_event_service import ClientEventService
from backend.services.client_service import ClientService


class DocumentValidationService:
    """Business rules for reviewing and assigning incoming documents."""

    ALLOWED_CATEGORIES = {
        "Juridique",
        "Fiscalité",
        "Comptabilité",
        "Social",
        "Banque",
        "Non classés",
    }

    def __init__(self, session: Session):
        self.session = session
        self.client_service = ClientService(session)
        self.document_repository = DocumentRepository(session)
        self.classification_repository = DocumentClassificationRepository(
            session
        )
        self.document_event_repository = DocumentEventRepository(session)
        self.client_event_service = ClientEventService(session)

    @classmethod
    def _normalize_category(cls, category: str | None) -> str | None:
        if category is None:
            return None

        category = category.strip()

        if category in {"", "Non classés"}:
            return None

        if category not in cls.ALLOWED_CATEGORIES:
            raise ValueError("Catégorie de document invalide.")

        return category

    def validate_document(
        self,
        current_user: User,
        document_id: int,
        client_id: int,
        *,
        category: str | None = None,
        classification_id: int | None = None,
    ):
        """Assign an incoming document to an accessible client."""

        client = self.client_service.get_client(current_user, client_id)

        if client is None:
            raise PermissionError(
                "Entreprise introuvable ou accès non autorisé."
            )

        document = self.document_repository.get_by_id(document_id)

        if document is None:
            raise ValueError("Document introuvable.")

        if document.status != DocumentStatus.TO_REVIEW:
            raise ValueError("Ce document n'est plus en attente de validation.")

        if document.client_id is not None:
            raise ValueError("Ce document est déjà affecté à une entreprise.")

        normalized_category = self._normalize_category(category)

        classification = None
        decision = None

        if classification_id is not None:
            classification = self.classification_repository.get_by_id(
                classification_id
            )

            if classification is None:
                raise ValueError("Proposition de classification introuvable.")

            if classification.document_id != document.id:
                raise ValueError(
                    "Cette proposition ne correspond pas au document."
                )

            if classification.decision != ClassificationDecision.PENDING:
                raise ValueError(
                    "Cette proposition a déjà été examinée."
                )

            if classification.proposed_client_id is None:
                raise ValueError(
                    "Aucun client n'a été proposé. "
                    "Utilisez l'affectation manuelle sans classification_id."
                )

            decision = (
                ClassificationDecision.ACCEPTED
                if classification.proposed_client_id == client.id
                else ClassificationDecision.CORRECTED
            )

        old_values = {
            "client_id": document.client_id,
            "status": document.status.value,
            "category": document.category,
        }

        # Affecter le client avant de passer le statut à CLASSIFIED.
        document.client_id = client.id
        document.category = normalized_category
        document.status = DocumentStatus.CLASSIFIED
        self.session.flush()

        # Enregistrer la décision uniquement si une proposition existe.
        if classification is not None:
            self.classification_repository.record_decision(
                classification_id=classification.id,
                decision=decision,
                reviewer_id=current_user.id,
            )

        new_values = {
            "client_id": document.client_id,
            "status": document.status.value,
            "category": document.category,
        }

        metadata = {
            "company_name": client.company_name,
            "classification_id": classification.id if classification else None,
            "decision": decision.value if decision else "MANUAL_ASSIGNMENT",
        }

        self.document_event_repository.create(
            document_id=document.id,
            actor_user_id=current_user.id,
            event_type="DOCUMENT_VALIDATED",
            old_values=old_values,
            new_values=new_values,
            event_metadata=metadata,
        )

        self.client_event_service.create_event(
            current_user,
            client.id,
            "DOCUMENT_CLASSIFIED",
            old_values=old_values,
            new_values=new_values,
            event_metadata={
                **metadata,
                "document_id": document.id,
            },
        )

        return document

    def reject_classification(
        self,
        current_user: User,
        classification_id: int,
    ):
        """Reject a pending proposal without assigning the document."""

        self.client_service._ensure_active_user(current_user)

        classification = self.classification_repository.get_by_id(
            classification_id
        )

        if classification is None:
            raise ValueError("Proposition de classification introuvable.")

        if classification.decision != ClassificationDecision.PENDING:
            raise ValueError("Cette proposition a déjà été examinée.")

        document = self.document_repository.get_by_id(
            classification.document_id
        )

        if document is None:
            raise ValueError("Document introuvable.")

        if document.client_id is not None:
            raise ValueError(
                "Le document est déjà affecté à une entreprise."
            )

        if document.status != DocumentStatus.TO_REVIEW:
            raise ValueError(
                "Le document n'est plus en attente de validation."
            )

        self.classification_repository.record_decision(
            classification_id=classification.id,
            decision=ClassificationDecision.REJECTED,
            reviewer_id=current_user.id,
        )

        self.document_event_repository.create(
            document_id=document.id,
            actor_user_id=current_user.id,
            event_type="CLASSIFICATION_REJECTED",
            old_values={
                "decision": ClassificationDecision.PENDING.value,
            },
            new_values={
                "decision": ClassificationDecision.REJECTED.value,
            },
            event_metadata={
                "classification_id": classification.id,
                "proposed_client_id": classification.proposed_client_id,
            },
        )

        return classification
