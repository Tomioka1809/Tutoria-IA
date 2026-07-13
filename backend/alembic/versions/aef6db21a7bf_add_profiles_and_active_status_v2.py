"""add_profiles_and_active_status_v2

Revision ID: aef6db21a7bf
Revises: f1f26b8fdb60
Create Date: 2026-07-10 19:40:06.477041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aef6db21a7bf'
down_revision: Union[str, Sequence[str], None] = 'f1f26b8fdb60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add column is_active to users if it doesn't exist
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'is_active' not in columns:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))

    # 2. Create tables
    op.create_table('motivational_quotes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_motivational_quotes_id'), 'motivational_quotes', ['id'], unique=False)
    
    op.create_table('admin_profiles',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('administrative_position', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id')
    )
    
    op.create_table('student_profiles',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('student_code', sa.String(length=50), nullable=False),
    sa.Column('current_semester', sa.Integer(), nullable=True),
    sa.Column('phone_number', sa.String(length=20), nullable=True),
    sa.Column('academic_status', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id')
    )
    
    op.create_table('tutor_profiles',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('tutor_code', sa.String(length=50), nullable=False),
    sa.Column('phone_number', sa.String(length=20), nullable=True),
    sa.Column('max_capacity', sa.Integer(), nullable=False, server_default='15'),
    sa.Column('expertise_areas', sa.String(length=500), nullable=True),
    sa.Column('office_location', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('tutor_code')
    )

    # 3. Add columns to tutor_assignments
    op.add_column('tutor_assignments', sa.Column('academic_period', sa.String(length=50), nullable=False, server_default='2026-1'))
    op.add_column('tutor_assignments', sa.Column('assignment_method', sa.String(length=50), nullable=False, server_default='manual'))
    op.add_column('tutor_assignments', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))
    op.create_index(op.f('ix_tutor_assignments_academic_period'), 'tutor_assignments', ['academic_period'], unique=False)
    op.create_unique_constraint('uix_assignment_period', 'tutor_assignments', ['student_id', 'tutor_id', 'service_type_id', 'academic_period'])

    # 4. Migrate existing data
    users_table = sa.table('users',
        sa.column('id', sa.Integer),
        sa.column('full_name', sa.String),
        sa.column('student_code', sa.String),
        sa.column('role', sa.String)
    )
    
    # Query all users
    users = bind.execute(users_table.select()).fetchall()
    
    # Insert profiles
    for u in users:
        role = u.role
        if role == 'estudiante':
            bind.execute(
                sa.text(
                    "INSERT INTO student_profiles (user_id, full_name, student_code, current_semester, phone_number, academic_status) "
                    "VALUES (:user_id, :full_name, :student_code, :current_semester, :phone_number, :academic_status)"
                ),
                {
                    "user_id": u.id,
                    "full_name": u.full_name or "",
                    "student_code": u.student_code or "123456",
                    "current_semester": 1,
                    "phone_number": None,
                    "academic_status": "regular"
                }
            )
        elif role == 'tutor':
            bind.execute(
                sa.text(
                    "INSERT INTO tutor_profiles (user_id, full_name, tutor_code, phone_number, max_capacity, expertise_areas, office_location) "
                    "VALUES (:user_id, :full_name, :tutor_code, :phone_number, :max_capacity, :expertise_areas, :office_location)"
                ),
                {
                    "user_id": u.id,
                    "full_name": u.full_name or "",
                    "tutor_code": f"TUT-{u.id}",
                    "phone_number": None,
                    "max_capacity": 15,
                    "expertise_areas": None,
                    "office_location": None
                }
            )
        elif role == 'admin':
            bind.execute(
                sa.text(
                    "INSERT INTO admin_profiles (user_id, full_name, administrative_position) "
                    "VALUES (:user_id, :full_name, :administrative_position)"
                ),
                {
                    "user_id": u.id,
                    "full_name": u.full_name or "",
                    "administrative_position": None
                }
            )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraints and indexes
    op.drop_constraint('uix_assignment_period', 'tutor_assignments', type_='unique')
    op.drop_index(op.f('ix_tutor_assignments_academic_period'), table_name='tutor_assignments')
    op.drop_column('tutor_assignments', 'created_at')
    op.drop_column('tutor_assignments', 'assignment_method')
    op.drop_column('tutor_assignments', 'academic_period')
    
    op.drop_table('tutor_profiles')
    op.drop_table('student_profiles')
    op.drop_table('admin_profiles')
    op.drop_index(op.f('ix_motivational_quotes_id'), table_name='motivational_quotes')
    op.drop_table('motivational_quotes')
