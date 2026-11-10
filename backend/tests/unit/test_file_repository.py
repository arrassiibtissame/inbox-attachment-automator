import pytest
from sqlalchemy.exc import IntegrityError

from backend.database.repositories.file_repository import FileRepository


def create_file(repository, **overrides):
    data = {
        "original_filename": "invoice.pdf",
        "stored_filename": "file_001.pdf",
        "storage_path": "storage/files/file_001.pdf",
        "sha256": "a" * 64,
        "extension": ".pdf",
        "size_bytes": 1024,
        "mime_type": "application/pdf",
    }

    data.update(overrides)
    return repository.create(**data)


def test_create_file(db_session):
    repository = FileRepository(db_session)

    file = create_file(repository)

    assert file.id is not None
    assert file.original_filename == "invoice.pdf"
    assert file.stored_filename == "file_001.pdf"
    assert file.sha256 == "a" * 64
    assert file.size_bytes == 1024
    assert file.mime_type == "application/pdf"


def test_create_file_without_mime_type(db_session):
    repository = FileRepository(db_session)

    file = create_file(repository, mime_type=None)

    assert file.mime_type is None


def test_get_by_id(db_session):
    repository = FileRepository(db_session)
    file = create_file(repository)

    result = repository.get_by_id(file.id)

    assert result is not None
    assert result.sha256 == file.sha256


def test_get_by_id_returns_none_when_not_found(db_session):
    repository = FileRepository(db_session)

    assert repository.get_by_id(999) is None


def test_get_by_sha256(db_session):
    repository = FileRepository(db_session)
    file = create_file(repository)

    result = repository.get_by_sha256("a" * 64)

    assert result is not None
    assert result.id == file.id


def test_get_by_sha256_returns_none_when_not_found(db_session):
    repository = FileRepository(db_session)

    assert repository.get_by_sha256("b" * 64) is None


def test_exists_by_sha256(db_session):
    repository = FileRepository(db_session)
    create_file(repository)

    assert repository.exists_by_sha256("a" * 64) is True
    assert repository.exists_by_sha256("b" * 64) is False


def test_list_all_returns_files_newest_first(db_session):
    repository = FileRepository(db_session)

    first_file = create_file(
        repository,
        original_filename="first.pdf",
        sha256="a" * 64,
    )

    second_file = create_file(
        repository,
        original_filename="second.pdf",
        stored_filename="file_002.pdf",
        sha256="b" * 64,
    )

    results = repository.list_all()

    assert len(results) == 2
    assert {file.id for file in results} == {
        first_file.id,
        second_file.id,
    }
    assert results[0].created_at >= results[1].created_at


def test_duplicate_sha256_is_rejected(db_session):
    repository = FileRepository(db_session)
    create_file(repository)

    with pytest.raises(IntegrityError):
        create_file(
            repository,
            original_filename="duplicate.pdf",
            stored_filename="duplicate.pdf",
        )

    db_session.rollback()


def test_zero_size_file_is_rejected(db_session):
    repository = FileRepository(db_session)

    with pytest.raises(IntegrityError):
        create_file(repository, size_bytes=0)

    db_session.rollback()


def test_invalid_sha256_length_is_rejected(db_session):
    repository = FileRepository(db_session)

    with pytest.raises(IntegrityError):
        create_file(repository, sha256="invalid")

    db_session.rollback()