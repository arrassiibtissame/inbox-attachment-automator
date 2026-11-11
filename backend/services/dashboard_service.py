from sqlalchemy import and_, func, or_, select

from backend.database.models import (
    Client,
    Document,
    DocumentReceipt,
    DocumentStatus,
    File,
    ReceiptSource,
    User,
    UserRole,
)


class DashboardService:
    """Fournit les statistiques du tableau de bord selon le rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â´le."""

    def __init__(self, session):
        self.session = session

    def _ensure_active_user(self, current_user):
        if current_user is None or not current_user.is_active:
            raise PermissionError("Utilisateur inactif ou non authentifiÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©.")

        if current_user.role not in (UserRole.ADMIN, UserRole.EMPLOYEE):
            raise PermissionError("RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â´le utilisateur non autorisÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©.")

    def _visible_documents_filter(self, current_user):
        """Tous voient les documents ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  vÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©rifier.
        Les employÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©s voient uniquement leurs documents classÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©s.
        """
        if current_user.role == UserRole.ADMIN:
            return True

        own_client_ids = select(Client.id).where(
            Client.responsible_user_id == current_user.id
        )

        return or_(
            Document.status == DocumentStatus.TO_REVIEW,
            and_(
                Document.status == DocumentStatus.CLASSIFIED,
                Document.client_id.in_(own_client_ids),
            ),
        )

    def _count_received_documents(self, current_user, source=None):
        statement = (
            select(func.count(func.distinct(Document.id)))
            .select_from(Document)
            .join(
                DocumentReceipt,
                DocumentReceipt.document_id == Document.id,
            )
            .where(self._visible_documents_filter(current_user))
        )

        if source is not None:
            statement = statement.where(
                DocumentReceipt.source == source
            )

        return self.session.scalar(statement) or 0

    def get_statistics(self, current_user):
        """Retourne les statistiques visibles par l'utilisateur."""
        self._ensure_active_user(current_user)

        clients_query = select(func.count(Client.id)).where(
            Client.is_active.is_(True)
        )

        if current_user.role == UserRole.EMPLOYEE:
            clients_query = clients_query.where(
                Client.responsible_user_id == current_user.id
            )

        active_clients = self.session.scalar(clients_query) or 0

        pending_documents = self.session.scalar(
            select(func.count(Document.id)).where(
                Document.status == DocumentStatus.TO_REVIEW
            )
        ) or 0

        classified_query = (
            select(func.count(Document.id))
            .select_from(Document)
            .outerjoin(Client, Document.client_id == Client.id)
            .where(Document.status == DocumentStatus.CLASSIFIED)
        )

        if current_user.role == UserRole.EMPLOYEE:
            classified_query = classified_query.where(
                Client.responsible_user_id == current_user.id
            )

        classified_documents = self.session.scalar(
            classified_query
        ) or 0

        return {
            "active_clients": active_clients,
            "documents_received": self._count_received_documents(
                current_user
            ),
            "documents_to_review": pending_documents,
            "classified_documents": classified_documents,
            "gmail_received": self._count_received_documents(
                current_user,
                ReceiptSource.GMAIL,
            ),
            "whatsapp_received": self._count_received_documents(
                current_user,
                ReceiptSource.WHATSAPP,
            ),
        }

    def get_recent_documents(self, current_user, limit=5):
        """Retourne les derniÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨res rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©ceptions, sans doublonner les documents."""
        self._ensure_active_user(current_user)

        if limit is not None:
            limit = max(1, min(int(limit), 50))

        statement = (
            select(DocumentReceipt, File, Document, Client.company_name)
            .join(
                Document,
                DocumentReceipt.document_id == Document.id,
            )
            .join(
                File,
                DocumentReceipt.file_id == File.id,
            )
            .outerjoin(Client, Document.client_id == Client.id)
            .where(self._visible_documents_filter(current_user))
            .order_by(
                DocumentReceipt.received_at.desc(),
                DocumentReceipt.id.desc(),
            )
        )

        rows = self.session.execute(statement).all()

        recent_documents = []
        seen_document_ids = set()

        for receipt, file_record, document, company_name in rows:
            if document.id in seen_document_ids:
                continue

            seen_document_ids.add(document.id)

            recent_documents.append({
                "document_id": document.id,
                "file_id": file_record.id,
                "name": file_record.original_filename,
                "path": file_record.storage_path,
                "size_bytes": file_record.size_bytes,
                "date": receipt.received_at,
                "type": document.document_type or "Autre",
                "status": document.status.value,
                "source": receipt.source.value,
                "client_name": company_name,
            })

            if limit is not None and len(recent_documents) >= limit:
                break

        return recent_documents

    def get_documents(self, current_user):
        """Retourner tous les documents visibles par l'utilisateur."""
        return self.get_recent_documents(current_user, limit=None)

    def get_employee_workload(self, current_user):
        """Retourne la charge de travail des employÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©s, pour l'ADMIN seulement."""
        self._ensure_active_user(current_user)

        if current_user.role != UserRole.ADMIN:
            raise PermissionError(
                "Seul l'administrateur peut consulter la charge des employÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©s."
            )

        employees = self.session.scalars(
            select(User)
            .where(
                User.role == UserRole.EMPLOYEE,
                User.is_active.is_(True),
            )
            .order_by(User.full_name)
        ).all()

        client_counts = dict(
            self.session.execute(
                select(
                    Client.responsible_user_id,
                    func.count(Client.id),
                )
                .where(Client.is_active.is_(True))
                .group_by(Client.responsible_user_id)
            ).all()
        )

        classified_counts = dict(
            self.session.execute(
                select(
                    Client.responsible_user_id,
                    func.count(Document.id),
                )
                .join(Document, Document.client_id == Client.id)
                .where(Document.status == DocumentStatus.CLASSIFIED)
                .group_by(Client.responsible_user_id)
            ).all()
        )

        pending_counts = dict(
            self.session.execute(
                select(
                    Client.responsible_user_id,
                    func.count(Document.id),
                )
                .join(Document, Document.client_id == Client.id)
                .where(Document.status == DocumentStatus.TO_REVIEW)
                .group_by(Client.responsible_user_id)
            ).all()
        )

        return [
            {
                "employee_id": employee.id,
                "employee_name": employee.full_name,
                "active_clients": client_counts.get(employee.id, 0),
                "classified_documents": classified_counts.get(
                    employee.id, 0
                ),
                "documents_to_review": pending_counts.get(
                    employee.id, 0
                ),
            }
            for employee in employees
        ]

    def get_dashboard_data(self, current_user, recent_limit=5):
        """Retourne toutes les donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©cessaires ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  l'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©cran."""
        self._ensure_active_user(current_user)

        return {
            "statistics": self.get_statistics(current_user),
            "recent_documents": self.get_recent_documents(
                current_user,
                recent_limit,
            ),
            "documents_to_process": self.get_documents_to_process(
                current_user,
            ),
            "employee_workload": (
                self.get_employee_workload(current_user)
                if current_user.role == UserRole.ADMIN
                else []
            ),
        }

    def get_documents_to_process(self, current_user):
        """Retourne les documents non identifiÃƒÂ©s, en attente, en retard et pris en charge."""
        from datetime import datetime, timezone
        from backend.database.models import (
            DocumentClassification,
            ClassificationDecision,
            ReviewClaim,
        )

        self._ensure_active_user(current_user)

        documents = self.session.scalars(
            select(Document)
            .where(Document.status == DocumentStatus.TO_REVIEW)
            .order_by(Document.created_at.desc(), Document.id.desc())
        ).all()

        document_ids = [document.id for document in documents]

        classifications = []
        receipts = []
        claims = []

        if document_ids:
            classifications = self.session.scalars(
                select(DocumentClassification)
                .where(DocumentClassification.document_id.in_(document_ids))
                .order_by(
                    DocumentClassification.created_at.desc(),
                    DocumentClassification.id.desc(),
                )
            ).all()

            receipts = self.session.scalars(
                select(DocumentReceipt)
                .where(DocumentReceipt.document_id.in_(document_ids))
                .order_by(
                    DocumentReceipt.received_at.asc(),
                    DocumentReceipt.id.asc(),
                )
            ).all()

            claims = self.session.scalars(
                select(ReviewClaim)
                .where(
                    ReviewClaim.document_id.in_(document_ids),
                    ReviewClaim.expires_at > datetime.now(timezone.utc),
                )
            ).all()

        latest_classifications = {}
        for classification in classifications:
            latest_classifications.setdefault(
                classification.document_id,
                classification,
            )

        first_receipts = {}
        for receipt in receipts:
            first_receipts.setdefault(receipt.document_id, receipt)

        active_claims = {
            claim.document_id: claim
            for claim in claims
        }

        unidentified = []
        awaiting_validation = []
        overdue = []
        claimed = []

        now = datetime.now(timezone.utc)

        for document in documents:
            classification = latest_classifications.get(document.id)

            proposed_client_name = None

            if classification and classification.proposed_client_id:
                proposed_client = self.session.get(
                    Client,
                    classification.proposed_client_id,
                )
                if proposed_client:
                    proposed_client_name = proposed_client.company_name

            item = {
                "document_id": document.id,
                "proposed_client_name": proposed_client_name,
                "decision": (
                    classification.decision.value
                    if classification
                    else None
                ),
            }

            if document.client_id is None:
                unidentified.append(item)

            if (
                classification
                and classification.decision == ClassificationDecision.PENDING
            ):
                awaiting_validation.append(item)

            first_receipt = first_receipts.get(document.id)

            if first_receipt and first_receipt.received_at:
                received_at = first_receipt.received_at

                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=timezone.utc)

                age_hours = (now - received_at).total_seconds() / 3600

                if age_hours > 24:
                    overdue.append({
                        **item,
                        "age_hours": round(age_hours, 1),
                    })

            claim = active_claims.get(document.id)

            if claim:
                employee = self.session.get(User, claim.user_id)

                claimed.append({
                    **item,
                    "claimed_by": employee.full_name if employee else None,
                    "claim_expires_at": claim.expires_at,
                })

        return {
            "unidentified": unidentified,
            "awaiting_validation": awaiting_validation,
            "overdue": overdue,
            "claimed": claimed,
        }