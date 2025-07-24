"""
add instrument upload tables

Revision ID: 0002_add_instrument_upload
Revises: 0001_initial
Create Date: 2023-01-01 00:01:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_add_instrument_upload'
down_revision = '0001_initial'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'upload_history',
        sa.Column('upload_id', sa.Integer(), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('checksum', sa.String(), nullable=False),
        sa.Column('uploaded_by', sa.String(), nullable=True),
        sa.Column('upload_timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('schema_version', sa.String(), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=False),
        sa.Column('valid_rows', sa.Integer(), nullable=False),
        sa.Column('invalid_rows', sa.Integer(), nullable=False),
    )

    op.create_table(
        'raw_instruments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('upload_id', sa.Integer(), nullable=False),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['upload_id'], ['upload_history.upload_id']),
    )
    op.create_index('ix_raw_instruments_upload_id', 'raw_instruments', ['upload_id'])

    op.create_table(
        'validated_instruments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('upload_id', sa.Integer(), nullable=False),
        sa.Column('instrument_id', sa.String(), nullable=False),
        sa.Column('borrower_id', sa.String(), nullable=False),
        sa.Column('asset_class', sa.String(), nullable=False),
        sa.Column('classification_category', sa.String(), nullable=False),
        sa.Column('measurement_basis', sa.String(), nullable=False),
        sa.Column('off_balance_flag', sa.Boolean(), nullable=False),
        sa.Column('pd_12m', sa.Float(), nullable=False),
        sa.Column('pd_lifetime', sa.Float(), nullable=False),
        sa.Column('lgd', sa.Float(), nullable=False),
        sa.Column('ead', sa.Float(), nullable=False),
        sa.Column('sicr_flag', sa.Boolean(), nullable=False),
        sa.Column('eir', sa.Float(), nullable=False),
        sa.Column('collateral_flag', sa.Boolean(), nullable=False),
        sa.Column('collateral_type', sa.String(), nullable=True),
        sa.Column('collateral_value', sa.Numeric(), nullable=True),
        sa.Column('appraisal_date', sa.Date(), nullable=True),
        sa.Column('drawdown_date', sa.Date(), nullable=False),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['upload_id'], ['upload_history.upload_id']),
    )
    op.create_index('ix_validated_instruments_upload_id', 'validated_instruments', ['upload_id'])
    op.create_index('ix_validated_instruments_instrument_id', 'validated_instruments', ['instrument_id'])

def downgrade():
    op.drop_index('ix_validated_instruments_instrument_id', table_name='validated_instruments')
    op.drop_index('ix_validated_instruments_upload_id', table_name='validated_instruments')
    op.drop_table('validated_instruments')
    op.drop_index('ix_raw_instruments_upload_id', table_name='raw_instruments')
    op.drop_table('raw_instruments')
    op.drop_table('upload_history')