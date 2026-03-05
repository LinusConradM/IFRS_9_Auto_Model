"""Update ccf_config table structure

Revision ID: update_ccf_config
Revises: update_staging_override
Create Date: 2026-03-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_ccf_config'
down_revision = 'update_staging_override'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old table and recreate with new structure
    op.drop_table('ccf_config')
    
    # Create new ccf_config table (using string for facility_type to avoid enum issues)
    op.create_table('ccf_config',
        sa.Column('config_id', sa.String(length=50), nullable=False),
        sa.Column('facility_type', sa.String(length=50), nullable=False),
        sa.Column('ccf_value', sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('updated_by', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('config_id')
    )


def downgrade():
    # Drop new table
    op.drop_table('ccf_config')
    
    # Recreate old table structure
    op.create_table('ccf_config',
        sa.Column('config_id', sa.String(length=50), nullable=False),
        sa.Column('facility_type', sa.String(length=50), nullable=False),
        sa.Column('default_ccf', sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column('calibration_source', sa.String(length=100), nullable=True),
        sa.Column('calibration_date', sa.Date(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('config_id')
    )
