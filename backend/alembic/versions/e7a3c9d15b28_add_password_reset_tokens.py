"""Add password_reset_tokens

Los codigos de recuperacion vivian en un diccionario en memoria del proceso: se
perdian en cada reinicio, no se compartian entre workers y no habia donde llevar la
cuenta de intentos fallidos. Esta tabla les da almacenamiento compartido y persistente.

Revision ID: e7a3c9d15b28
Revises: d5b2c8e31f74
Create Date: 2026-08-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a3c9d15b28'
down_revision: Union[str, Sequence[str], None] = 'd5b2c8e31f74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        # Se guarda el hash del codigo, nunca el codigo en claro.
        sa.Column('code_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_password_reset_tokens_id'), 'password_reset_tokens', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_password_reset_tokens_email'),
        'password_reset_tokens',
        ['email'],
        unique=False,
    )
    # La consulta caliente es "el codigo vigente de este correo".
    op.create_index(
        'ix_password_reset_tokens_email_active',
        'password_reset_tokens',
        ['email', 'is_active'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_password_reset_tokens_email_active', table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_email'), table_name='password_reset_tokens')
    op.drop_index(op.f('ix_password_reset_tokens_id'), table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
