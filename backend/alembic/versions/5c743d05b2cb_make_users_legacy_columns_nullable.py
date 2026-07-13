"""make_users_legacy_columns_nullable

Revision ID: 5c743d05b2cb
Revises: aef6db21a7bf
Create Date: 2026-07-10 19:47:15.549695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c743d05b2cb'
down_revision: Union[str, Sequence[str], None] = 'aef6db21a7bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    The 'full_name', 'student_code' and 'school' columns were part of the
    original schema but are now kept for backward compatibility only.
    Profile data is stored in student_profiles/tutor_profiles/admin_profiles.
    These columns are made nullable with an empty default so new User inserts
    (which no longer include these fields) don't violate NOT NULL constraints.
    """
    op.alter_column('users', 'full_name',
        existing_type=sa.String(length=255),
        nullable=True,
        server_default=''
    )
    op.alter_column('users', 'student_code',
        existing_type=sa.String(length=50),
        nullable=True,
    )
    # school was already nullable
    op.alter_column('users', 'school',
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Note: reverting nullable->not null requires all rows to have a value
    op.alter_column('users', 'full_name',
        existing_type=sa.String(length=255),
        nullable=False,
        server_default=None
    )
