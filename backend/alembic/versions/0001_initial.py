"""
Initial database schema migration.

Revision ID: 0001_initial
Revises: 
Create Date: 2023-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'loan_book_versions',
        sa.Column('version_id', sa.Integer(), primary_key=True),
        sa.Column('snapshot_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
    )

    op.create_table(
        'loan_portfolio',
        sa.Column('loan_id', sa.String(), primary_key=True),
        sa.Column('borrower_id', sa.String(), nullable=False),
        sa.Column('drawdown_date', sa.Date(), nullable=False),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.Column('pd_12m', sa.Float(), nullable=True),
        sa.Column('pd_lifetime', sa.Float(), nullable=True),
        sa.Column('lgd', sa.Float(), nullable=True),
        sa.Column('ead', sa.Float(), nullable=True),
        sa.Column('sicr_flag', sa.Boolean(), nullable=True),
        sa.Column('stage', sa.Integer(), nullable=True),
        sa.Column('impairment_allowance', sa.Numeric(), nullable=True),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['loan_book_versions.version_id']),
    )
    op.create_index('ix_loan_portfolio_borrower_id', 'loan_portfolio', ['borrower_id'])
    op.create_index('ix_loan_portfolio_drawdown_date', 'loan_portfolio', ['drawdown_date'])
    op.create_index('ix_loan_portfolio_maturity_date', 'loan_portfolio', ['maturity_date'])
    op.create_index('ix_loan_portfolio_sicr_flag', 'loan_portfolio', ['sicr_flag'])
    op.create_index('ix_loan_portfolio_stage', 'loan_portfolio', ['stage'])

    op.create_table(
        'collateral_information',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('loan_id', sa.String(), nullable=False),
        sa.Column('collateral_type', sa.String(), nullable=False),
        sa.Column('value', sa.Numeric(), nullable=False),
        sa.Column('appraisal_date', sa.Date(), nullable=False),
        sa.Column('ltv', sa.Float(), nullable=True),
        sa.Column('guarantee_amount', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loan_portfolio.loan_id']),
    )
    op.create_index('ix_collateral_information_loan_id', 'collateral_information', ['loan_id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=True),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('performed_by', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('doc_type', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('linked_loan_id', sa.String(), nullable=False),
        sa.Column('uploaded_by', sa.String(), nullable=False),
        sa.Column('checksum', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['linked_loan_id'], ['loan_portfolio.loan_id']),
    )
    op.create_index('ix_attachments_linked_loan_id', 'attachments', ['linked_loan_id'])

    op.create_table(
        'instrument_staging',
        sa.Column('instrument_id', sa.String(), primary_key=True),
        sa.Column('current_stage', sa.Integer(), nullable=False),
        sa.Column('sicr_flag', sa.Boolean(), nullable=False),
        sa.Column('default_flag', sa.Boolean(), nullable=False),
        sa.Column('days_past_due', sa.Integer(), nullable=False),
        sa.Column('last_stage_change', sa.DateTime(timezone=True), nullable=False),
        sa.Column('override_reason', sa.String(), nullable=True),
        sa.Column('classified_by', sa.String(), nullable=True),
    )

    op.create_table(
        'staging_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('instrument_id', sa.String(), nullable=False),
        sa.Column('from_stage', sa.Integer(), nullable=False),
        sa.Column('to_stage', sa.Integer(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('changed_by', sa.String(), nullable=False),
        sa.Column('trigger_type', sa.Enum('auto', 'manual', name='trigger_type'), nullable=False),
        sa.Column('rationale', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['instrument_id'], ['instrument_staging.instrument_id']),
    )
    op.create_index('ix_staging_history_instrument_id', 'staging_history', ['instrument_id'])

    op.create_table(
        'scenario_assumptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('scenario', sa.Enum('base', 'adverse', 'optimistic', name='scenario_type'), nullable=False),
        sa.Column('unemployment', sa.Float(), nullable=True),
        sa.Column('gdp', sa.Float(), nullable=True),
        sa.Column('interest_rate', sa.Float(), nullable=True),
        sa.Column('scenario_weights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'approval_workflows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('loan_id', sa.String(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('submitted', 'reviewed', 'approved', 'published', name='approval_status'), nullable=False, server_default='submitted'),
        sa.Column('reviewer', sa.String(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loan_portfolio.loan_id']),
        sa.ForeignKeyConstraint(['version_id'], ['loan_book_versions.version_id']),
    )
    op.create_index('ix_approval_workflows_loan_id', 'approval_workflows', ['loan_id'])

    op.create_table(
        'impairment_calculations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('loan_id', sa.String(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('calculated_by', sa.String(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ptp_ecl', sa.Numeric(), nullable=False),
        sa.Column('lifetime_ecl', sa.Numeric(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['loan_id'], ['loan_portfolio.loan_id']),
        sa.ForeignKeyConstraint(['version_id'], ['loan_book_versions.version_id']),
    )
    op.create_index('ix_impairment_calculations_loan_id', 'impairment_calculations', ['loan_id'])

    op.create_table(
        'ecl_computation_results',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('instrument_id', sa.String(), nullable=False),
        sa.Column('stage', sa.Integer(), nullable=False),
        sa.Column('pd', sa.Float(), nullable=False),
        sa.Column('lgd', sa.Float(), nullable=False),
        sa.Column('ead', sa.Float(), nullable=False),
        sa.Column('eir', sa.Float(), nullable=False),
        sa.Column('ecl_amount', sa.Numeric(), nullable=False),
        sa.Column('discounted', sa.Numeric(), nullable=False),
        sa.Column('scenario_version', sa.Integer(), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('scenario_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['instrument_id'], ['instrument_staging.instrument_id']),
        sa.ForeignKeyConstraint(['scenario_version'], ['scenario_assumptions.id']),
    )
    op.create_index('ix_ecl_computation_results_instrument_id', 'ecl_computation_results', ['instrument_id'])

    op.create_table(
        'provision_matrix_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('segment_keys', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('buckets', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('base_loss_rates', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('macro_adjustment_model', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'ecl_forecasts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('portfolio_id', sa.Integer(), nullable=False),
        sa.Column('forecast_horizon', sa.Integer(), nullable=False),
        sa.Column('scenario_weights', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('macro_inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ecl_curve_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('generated_by', sa.String(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['portfolio_id'], ['loan_book_versions.version_id']),
    )
    op.create_index('ix_ecl_forecasts_portfolio_id', 'ecl_forecasts', ['portfolio_id'])


def downgrade():
    op.drop_index('ix_ecl_forecasts_portfolio_id', table_name='ecl_forecasts')
    op.drop_table('ecl_forecasts')
    op.drop_table('provision_matrix_templates')
    op.drop_index('ix_ecl_computation_results_instrument_id', table_name='ecl_computation_results')
    op.drop_table('ecl_computation_results')
    op.drop_index('ix_impairment_calculations_loan_id', table_name='impairment_calculations')
    op.drop_table('impairment_calculations')
    op.drop_index('ix_approval_workflows_loan_id', table_name='approval_workflows')
    op.drop_table('approval_workflows')
    op.drop_table('scenario_assumptions')
    op.drop_index('ix_staging_history_instrument_id', table_name='staging_history')
    op.drop_table('staging_history')
    op.drop_table('instrument_staging')
    op.drop_index('ix_attachments_linked_loan_id', table_name='attachments')
    op.drop_table('attachments')
    op.drop_table('audit_logs')
    op.drop_index('ix_collateral_information_loan_id', table_name='collateral_information')
    op.drop_table('collateral_information')
    op.drop_index('ix_loan_portfolio_stage', table_name='loan_portfolio')
    op.drop_index('ix_loan_portfolio_sicr_flag', table_name='loan_portfolio')
    op.drop_index('ix_loan_portfolio_maturity_date', table_name='loan_portfolio')
    op.drop_index('ix_loan_portfolio_drawdown_date', table_name='loan_portfolio')
    op.drop_index('ix_loan_portfolio_borrower_id', table_name='loan_portfolio')
    op.drop_table('loan_portfolio')
    op.drop_table('loan_book_versions')