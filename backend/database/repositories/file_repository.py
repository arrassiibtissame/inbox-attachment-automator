from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from backend.database.models.file import File


class FileRepository:
    """Handles database operations related to stored files."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        original_filename: str,
        stored_filename: str,
        storage_path: str,
        sha256: str,
        extension: str,
        size_bytes: int,
        mime_type: str | None = None,
    ) -> File:
        file = File(
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            sha256=sha256,
            mime_type=mime_type,
            extension=extension,
            size_bytes=size_bytes,
        )

        self.session.add(file)
        self.session.flush()

        return file

    def get_by_id(self, file_id: int) -> File | None:
        return self.session.get(File, file_id)

    def get_by_sha256(self, sha256: str) -> File | None:
        statement = select(File).where(File.sha256 == sha256)
        return self.session.scalars(statement).one_or_none()

    def exists_by_sha256(self, sha256: str) -> bool:
        statement = select(exists().where(File.sha256 == sha256))
        return bool(self.session.scalar(statement))

    def list_all(self) -> list[File]:
        statement = select(File).order_by(File.created_at.desc())
        return list(self.session.scalars(statement).all())