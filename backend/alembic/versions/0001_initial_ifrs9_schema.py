"""initial IFRS9 schema

Revision ID: 0001_initial_ifrs9_schema
Revises: 
Create Date: 2023-01-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_ifrs9_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'loan_portfolio',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('borrower_id', sa.String(), nullable=False),
        sa.Column('loan_id', sa.String(), nullable=False),
        sa.Column('stage', sa.Integer(), nullable=False),
        sa.Column('pd', sa.Numeric(5, 4), nullable=False),
        sa.Column('lgd', sa.Numeric(5, 4), nullable=False),
        sa.Column('ead', sa.Numeric(14, 2), nullable=False),
        sa.Column('impairment', sa.Numeric(14, 2), nullable=True),
        sa.Column('drawdown_date', sa.Date(), nullable=False),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.Column('default_flag', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index(op.f('ix_loan_portfolio_borrower_id'), 'loan_portfolio', ['borrower_id'], unique=False)
    op.create_index(op.f('ix_loan_portfolio_loan_id'), 'loan_portfolio', ['loan_id'], unique=True)
    op.create_index(op.f('ix_loan_portfolio_stage'), 'loan_portfolio', ['stage'], unique=False)
    op.create_index(op.f('ix_loan_portfolio_drawdown_date'), 'loan_portfolio', ['drawdown_date'], unique=False)
    op.create_index(op.f('ix_loan_portfolio_maturity_date'), 'loan_portfolio', ['maturity_date'], unique=False)
    op.create_index(op.f('ix_loan_portfolio_default_flag'), 'loan_portfolio', ['default_flag'], unique=False)

    op.create_table(
        'collateral_information',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('value', sa.Numeric(14, 2), nullable=False),
        sa.Column('appraisal_date', sa.Date(), nullable=False),
        sa.Column('ltv', sa.Numeric(5, 4), nullable=False),
    )
    op.create_index(op.f('ix_collateral_information_loan_id'), 'collateral_information', ['loan_id'], unique=False)
    op.create_foreign_key(
        op.f('fk_collateral_information_loan_id_loan_portfolio'),
        'collateral_information', 'loan_portfolio', ['loan_id'], ['id'],
    )

    op.create_table(
        'loan_book_versions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_loan_book_versions_loan_id'), 'loan_book_versions', ['loan_id'], unique=False)
    op.create_foreign_key(
        op.f('fk_loan_book_versions_loan_id_loan_portfolio'),
        'loan_book_versions', 'loan_portfolio', ['loan_id'], ['id'],
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('actor', sa.String(), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)

    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('loan_id', sa.Integer(), nullable=True),
        sa.Column('borrower_id', sa.String(), nullable=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_attachments_loan_id'), 'attachments', ['loan_id'], unique=False)
    op.create_index(op.f('ix_attachments_borrower_id'), 'attachments', ['borrower_id'], unique=False)
    op.create_foreign_key(
        op.f('fk_attachments_loan_id_loan_portfolio'),
        'attachments', 'loan_portfolio', ['loan_id'], ['id'],
    )

    op.create_table(
        'approval_workflows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('loan_id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('assigned_reviewer', sa.String(), nullable=True),
        sa.Column('actioned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_approval_workflows_loan_id'), 'approval_workflows', ['loan_id'], unique=False)
    op.create_index(op.f('ix_approval_workflows_state'), 'approval_workflows', ['state'], unique=False)
    op.create_foreign_key(
        op.f('fk_approval_workflows_loan_id_loan_portfolio'),
        'approval_workflows', 'loan_portfolio', ['loan_id'], ['id'],
    )

    # roles for role-based access control
    op.execute("CREATE ROLE IF NOT EXISTS analyst;")
    op.execute("CREATE ROLE IF NOT EXISTS admin;")


def downgrade():
    op.drop_table('approval_workflows')
    op.drop_table('attachments')
    op.drop_table('audit_logs')
    op.drop_table('loan_book_versions')
    op.drop_table('collateral_information')
    op.drop_table('loan_portfolio')