"""Update staging_override table structure

Revision ID: update_staging_override
Revises: add_instrument_fields
Create Date: 2026-03-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_staging_override'
down_revision = 'add_instrument_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old table and recreate with new structure
    op.drop_table('staging_override')
    
    # Create new staging_override table (using existing Stage and OverrideStatus enums)
    op.create_table('staging_override',
        sa.Column('override_id', sa.String(length=50), nullable=False),
        sa.Column('instrument_id', sa.String(length=50), nullable=False),
        sa.Column('original_stage', sa.String(length=20), nullable=False),
        sa.Column('override_stage', sa.String(length=20), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('requested_by', sa.String(length=50), nullable=False),
        sa.Column('requested_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_by', sa.String(length=50), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_by', sa.String(length=50), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('workflow_id', sa.String(length=50), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('expired_at', sa.DateTime(), nullable=True),
        sa.Column('ecl_before_override', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('ecl_after_override', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('ecl_impact_amount', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['instrument_id'], ['financial_instrument.instrument_id'], ),
        sa.PrimaryKeyConstraint('override_id')
    )


def downgrade():
    # Drop new table
    op.drop_table('staging_override')
    
    # Recreate old table structure
    op.create_table('staging_override',
        sa.Column('override_id', sa.String(length=50), nullable=False),
        sa.Column('instrument_id', sa.String(length=50), nullable=False),
        sa.Column('current_stage', sa.String(length=20), nullable=False),
        sa.Column('requested_stage', sa.String(length=20), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('requester_id', sa.String(length=50), nullable=False),
        sa.Column('request_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('approver_id', sa.String(length=50), nullable=True),
        sa.Column('approval_date', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('ecl_impact_before', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column('ecl_impact_after', sa.Numeric(precision=18, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['instrument_id'], ['financial_instrument.instrument_id'], ),
        sa.PrimaryKeyConstraint('override_id')
    )
