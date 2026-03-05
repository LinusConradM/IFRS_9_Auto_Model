"""Add missing fields to financial_instrument table

Revision ID: add_instrument_fields
Revises: phase1_enhancements
Create Date: 2026-03-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_instrument_fields'
down_revision = 'phase1_enhancements'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to financial_instrument table (only those not already added by phase1_enhancements)
    op.add_column('financial_instrument', sa.Column('outstanding_balance', sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column('financial_instrument', sa.Column('current_ecl', sa.Numeric(precision=18, scale=2), nullable=True))
    op.add_column('financial_instrument', sa.Column('stage_override_active', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('financial_instrument', sa.Column('stage_override_reason', sa.Text(), nullable=True))


def downgrade():
    # Remove columns from financial_instrument table
    op.drop_column('financial_instrument', 'stage_override_reason')
    op.drop_column('financial_instrument', 'stage_override_active')
    op.drop_column('financial_instrument', 'current_ecl')
    op.drop_column('financial_instrument', 'outstanding_balance')
