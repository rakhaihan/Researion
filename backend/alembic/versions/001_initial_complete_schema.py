"""Initial complete schema (users + research + jobs).

Revision ID: 001_initial_complete
Revises:
Create Date: 2026-05-29

For fresh installs, creates all tables from SQLAlchemy metadata.
If upgrading from a pre-Alembic database, reset with:
  docker-compose down -v && docker-compose up --build
or run alembic stamp before manual migration.
"""

from typing import Sequence, Union

from alembic import op

from app.db import models  # noqa: F401
from app.db.database import Base

revision: str = "001_initial_complete"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
