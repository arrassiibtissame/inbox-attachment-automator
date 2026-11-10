
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from backend.database.models.review_claim import ReviewClaim


class ReviewClaimRepository:
    """Handles temporary document review reservations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        document_id: int,
        user_id: int,
        duration_minutes: int = 15,
    ) -> ReviewClaim:
        if duration_minutes <= 0:
            raise ValueError("Claim duration must be positive.")

        now = datetime.now(timezone.utc)

        existing_claim = self.get_by_document(document_id)

        if existing_claim is not None:
            expires_at = existing_claim.expires_at

            # SQLite may return timezone-naive datetimes.
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at > now:
                raise ValueError("This document is already claimed.")

            self.session.delete(existing_claim)
            self.session.flush()

        claim = ReviewClaim(
            document_id=document_id,
            user_id=user_id,
            claimed_at=now,
            expires_at=now + timedelta(minutes=duration_minutes),
        )

        self.session.add(claim)
        self.session.flush()

        return claim

    def get_by_document(
        self,
        document_id: int,
    ) -> ReviewClaim | None:
        statement = select(ReviewClaim).where(
            ReviewClaim.document_id == document_id
        )

        return self.session.scalars(statement).one_or_none()

    def get_by_user(self, user_id: int) -> list[ReviewClaim]:
        statement = (
            select(ReviewClaim)
            .where(ReviewClaim.user_id == user_id)
            .order_by(ReviewClaim.claimed_at.desc())
        )

        return list(self.session.scalars(statement).all())

    def list_active(self) -> list[ReviewClaim]:
        now = datetime.now(timezone.utc)

        statement = (
            select(ReviewClaim)
            .where(ReviewClaim.expires_at > now)
            .order_by(ReviewClaim.expires_at.asc())
        )

        return list(self.session.scalars(statement).all())

    def release(self, document_id: int) -> bool:
        claim = self.get_by_document(document_id)

        if claim is None:
            return False

        self.session.delete(claim)
        self.session.flush()

        return True

    def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)

        statement = delete(ReviewClaim).where(
            ReviewClaim.expires_at <= now
        )

        result = self.session.execute(statement)
        self.session.flush()

        return result.rowcount or 0
