"""Backfill default dev user for legacy rows without user_id.

Revision ID: 002_backfill_dev_user
Revises: 001_initial_complete
Create Date: 2026-05-29

Only needed when upgrading an existing database that had research_projects
without user_id. Fresh installs after 001 already include user_id.
This migration is a no-op if user_id column does not exist or all rows are set.
"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from passlib.context import CryptContext
revision: str = "002_backfill_dev_user"
down_revision: Union[str, None] = "001_initial_complete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "users" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("research_projects")}
    if "user_id" not in columns:
        return

    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd.hash("devpassword123")

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            INSERT INTO users (id, full_name, email, hashed_password, is_active, is_superuser)
            VALUES (:id, :full_name, :email, :hashed_password, true, true)
            ON CONFLICT (email) DO NOTHING
            """
        ),
        {
            "id": str(DEFAULT_USER_ID),
            "full_name": "Development User",
            "email": "dev@researion.local",
            "hashed_password": hashed,
        },
    )

    connection.execute(
        sa.text(
            """
            UPDATE research_projects
            SET user_id = :user_id
            WHERE user_id IS NULL
            """
        ),
        {"user_id": str(DEFAULT_USER_ID)},
    )


def downgrade() -> None:
    pass
