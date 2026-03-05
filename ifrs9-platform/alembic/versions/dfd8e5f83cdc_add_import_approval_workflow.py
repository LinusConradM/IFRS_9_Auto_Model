"""add_import_approval_workflow

Revision ID: dfd8e5f83cdc
Revises: a2164e1442c3
Create Date: 2026-03-04 19:05:58.194975

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dfd8e5f83cdc'
down_revision = 'a2164e1442c3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create import_status enum (check if exists first)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE importstatus AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create import_batch table
    op.create_table(
        'import_batch',
        sa.Column('import_id', sa.String(50), primary_key=True),
        sa.Column('import_type', sa.String(50), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='importstatus'), nullable=False, server_default='PENDING'),
        sa.Column('filename', sa.String(255)),
        sa.Column('file_format', sa.String(10)),
        sa.Column('records_processed', sa.Integer, default=0),
        sa.Column('records_valid', sa.Integer, default=0),
        sa.Column('records_invalid', sa.Integer, default=0),
        sa.Column('validation_errors', sa.JSON),
        sa.Column('submitted_by', sa.String(50), nullable=False),
        sa.Column('submitted_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_by', sa.String(50)),
        sa.Column('reviewed_at', sa.DateTime),
        sa.Column('review_notes', sa.Text)
    )
    
    # Create staged_instrument table
    op.create_table(
        'staged_instrument',
        sa.Column('staged_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('import_id', sa.String(50), sa.ForeignKey('import_batch.import_id'), nullable=False),
        sa.Column('instrument_id', sa.String(50), nullable=False),
        sa.Column('instrument_type', sa.String(50), nullable=False),
        sa.Column('customer_id', sa.String(50), nullable=False),
        sa.Column('origination_date', sa.Date, nullable=False),
        sa.Column('maturity_date', sa.Date, nullable=False),
        sa.Column('principal_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('outstanding_balance', sa.Numeric(18, 2)),
        sa.Column('interest_rate', sa.Numeric(8, 4), nullable=False),
        sa.Column('currency', sa.String(3), server_default='UGX'),
        sa.Column('days_past_due', sa.Integer, server_default='0'),
        sa.Column('is_poci', sa.Boolean, server_default='false'),
        sa.Column('is_forbearance', sa.Boolean, server_default='false'),
        sa.Column('is_watchlist', sa.Boolean, server_default='false'),
        sa.Column('customer_name', sa.String(255)),
        sa.Column('customer_type', sa.String(50)),
        sa.Column('customer_sector', sa.String(100)),
        sa.Column('customer_credit_rating', sa.String(20)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )
    
    # Create indexes
    op.create_index('idx_import_batch_status', 'import_batch', ['status'])
    op.create_index('idx_import_batch_submitted_by', 'import_batch', ['submitted_by'])
    op.create_index('idx_staged_instrument_import_id', 'staged_instrument', ['import_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_staged_instrument_import_id', 'staged_instrument')
    op.drop_index('idx_import_batch_submitted_by', 'import_batch')
    op.drop_index('idx_import_batch_status', 'import_batch')
    
    # Drop tables
    op.drop_table('staged_instrument')
    op.drop_table('import_batch')
    
    # Drop enum
    op.execute("DROP TYPE importstatus")
