
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.models.document import Document
from backend.database.models.review_claim import ReviewClaim
from backend.database.models.user import User, UserRole
from backend.database.repositories.review_claim_repository import (
    ReviewClaimRepository,
)


def create_user(db_session, email="employee@test.com"):
    user = User(
        full_name="Test Employee",
        email=email,
        password_hash="test_hash",
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.flush()
    return user


def create_document(db_session):
    document = Document()
    db_session.add(document)
    db_session.flush()
    return document


def test_create_claim(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)
    user = create_user(db_session)

    claim = repository.create(
        document_id=document.id,
        user_id=user.id,
        duration_minutes=15,
    )

    assert claim.id is not None
    assert claim.document_id == document.id
    assert claim.user_id == user.id
    assert claim.claimed_at.tzinfo is not None
    assert claim.expires_at > claim.claimed_at


def test_create_claim_with_default_duration(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)
    user = create_user(db_session)

    claim = repository.create(
        document_id=document.id,
        user_id=user.id,
    )

    duration = claim.expires_at - claim.claimed_at

    assert duration == timedelta(minutes=15)


def test_create_claim_rejects_non_positive_duration(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)
    user = create_user(db_session)

    with pytest.raises(ValueError, match="duration must be positive"):
        repository.create(
            document_id=document.id,
            user_id=user.id,
            duration_minutes=0,
        )


def test_get_by_document(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)
    user = create_user(db_session)

    claim = repository.create(
        document_id=document.id,
        user_id=user.id,
    )

    result = repository.get_by_document(document.id)

    assert result is not None
    assert result.id == claim.id


def test_get_by_document_returns_none_when_not_found(db_session):
    repository = ReviewClaimRepository(db_session)

    assert repository.get_by_document(999) is None


def test_get_by_user(db_session):
    repository = ReviewClaimRepository(db_session)

    document_one = create_document(db_session)
    document_two = create_document(db_session)
    user_one = create_user(db_session)
    user_two = create_user(db_session, "employee2@test.com")

    first = repository.create(
        document_id=document_one.id,
        user_id=user_one.id,
    )

    repository.create(
        document_id=document_two.id,
        user_id=user_two.id,
    )

    results = repository.get_by_user(user_one.id)

    assert len(results) == 1
    assert results[0].id == first.id


def test_list_active_excludes_expired_claims(db_session):
    repository = ReviewClaimRepository(db_session)

    active_document = create_document(db_session)
    expired_document = create_document(db_session)
    user = create_user(db_session)

    active_claim = repository.create(
        document_id=active_document.id,
        user_id=user.id,
    )

    expired_claim = ReviewClaim(
        document_id=expired_document.id,
        user_id=user.id,
        claimed_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=15),
    )
    db_session.add(expired_claim)
    db_session.flush()

    results = repository.list_active()

    assert len(results) == 1
    assert results[0].id == active_claim.id


def test_create_rejects_document_already_claimed(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)

    user_one = create_user(db_session)
    user_two = create_user(db_session, "employee2@test.com")

    repository.create(
        document_id=document.id,
        user_id=user_one.id,
    )

    with pytest.raises(ValueError, match="already claimed"):
        repository.create(
            document_id=document.id,
            user_id=user_two.id,
        )



def test_expired_claim_can_be_replaced(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)

    user_one = create_user(db_session)
    user_two = create_user(db_session, "employee2@test.com")

    expired_claim = ReviewClaim(
        document_id=document.id,
        user_id=user_one.id,
        claimed_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=15),
    )
    db_session.add(expired_claim)
    db_session.flush()

    new_claim = repository.create(
        document_id=document.id,
        user_id=user_two.id,
    )

    assert new_claim.user_id == user_two.id

    current_claim = repository.get_by_document(document.id)

    assert current_claim is not None
    assert current_claim.user_id == user_two.id
    assert current_claim.expires_at > current_claim.claimed_at



def test_release_claim(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)
    user = create_user(db_session)

    repository.create(
        document_id=document.id,
        user_id=user.id,
    )

    result = repository.release(document.id)

    assert result is True
    assert repository.get_by_document(document.id) is None


def test_release_returns_false_when_claim_does_not_exist(db_session):
    repository = ReviewClaimRepository(db_session)

    assert repository.release(999) is False


def test_delete_expired(db_session):
    repository = ReviewClaimRepository(db_session)
    user = create_user(db_session)

    expired_document = create_document(db_session)
    active_document = create_document(db_session)

    expired_claim = ReviewClaim(
        document_id=expired_document.id,
        user_id=user.id,
        claimed_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=15),
    )

    active_claim = repository.create(
        document_id=active_document.id,
        user_id=user.id,
    )

    db_session.add(expired_claim)
    db_session.flush()

    deleted_count = repository.delete_expired()

    assert deleted_count == 1
    assert repository.get_by_document(expired_document.id) is None
    assert repository.get_by_document(active_document.id).id == active_claim.id


def test_claim_requires_existing_document(db_session):
    repository = ReviewClaimRepository(db_session)
    user = create_user(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            document_id=999,
            user_id=user.id,
        )

    db_session.rollback()


def test_claim_requires_existing_user(db_session):
    repository = ReviewClaimRepository(db_session)
    document = create_document(db_session)

    with pytest.raises(IntegrityError):
        repository.create(
            document_id=document.id,
            user_id=999,
        )

    db_session.rollback()
