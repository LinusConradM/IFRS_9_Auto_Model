"""Phase 1 CFO Enhancements

Revision ID: phase1_enhancements
Revises: dfd8e5f83cdc
Create Date: 2026-03-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase1_enhancements'
down_revision = 'dfd8e5f83cdc'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # TASK 30: Enhanced Staging Engine
    # ========================================
    
    # Add qualitative SICR fields to financial_instrument
    op.add_column('financial_instrument', sa.Column('watchlist_status', sa.String(50), nullable=True))
    op.add_column('financial_instrument', sa.Column('is_restructured', sa.Boolean(), default=False))
    op.add_column('financial_instrument', sa.Column('restructuring_date', sa.Date(), nullable=True))
    op.add_column('financial_instrument', sa.Column('forbearance_granted', sa.Boolean(), default=False))
    op.add_column('financial_instrument', sa.Column('forbearance_date', sa.Date(), nullable=True))
    
    # Add sector risk rating to customer
    op.add_column('customer', sa.Column('sector_risk_rating', sa.String(20), nullable=True))
    
    # Add trigger details to stage_transition
    op.add_column('stage_transition', sa.Column('trigger_details', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('stage_transition', sa.Column('qualitative_indicators', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Create staging_override table
    op.create_table('staging_override',
        sa.Column('override_id', sa.String(50), nullable=False),
        sa.Column('instrument_id', sa.String(50), nullable=False),
        sa.Column('current_stage', sa.String(20), nullable=False),
        sa.Column('requested_stage', sa.String(20), nullable=False),
        sa.Column('justification', sa.Text(), nullable=False),
        sa.Column('requester_id', sa.String(50), nullable=False),
        sa.Column('request_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('approver_id', sa.String(50), nullable=True),
        sa.Column('approval_date', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # PENDING, APPROVED, REJECTED
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('ecl_impact_before', sa.Numeric(18, 2), nullable=True),
        sa.Column('ecl_impact_after', sa.Numeric(18, 2), nullable=True),
        sa.ForeignKeyConstraint(['instrument_id'], ['financial_instrument.instrument_id'], ),
        sa.PrimaryKeyConstraint('override_id')
    )
    op.create_index('ix_staging_override_instrument_id', 'staging_override', ['instrument_id'])
    op.create_index('ix_staging_override_status', 'staging_override', ['status'])
    
    # ========================================
    # TASK 31: Transition Matrix PD
    # ========================================
    
    # Create transition_matrix table
    op.create_table('transition_matrix',
        sa.Column('matrix_id', sa.String(50), nullable=False),
        sa.Column('portfolio_segment', sa.String(50), nullable=False),
        sa.Column('rating_from', sa.String(20), nullable=False),
        sa.Column('rating_to', sa.String(20), nullable=False),
        sa.Column('transition_probability', sa.Numeric(10, 8), nullable=False),
        sa.Column('observation_period_start', sa.Date(), nullable=False),
        sa.Column('observation_period_end', sa.Date(), nullable=False),
        sa.Column('calibration_date', sa.Date(), nullable=False),
        sa.Column('matrix_type', sa.String(10), nullable=False),  # PIT, TTC
        sa.Column('psi_value', sa.Numeric(8, 6), nullable=True),  # Population Stability Index
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('matrix_id')
    )
    op.create_index('ix_transition_matrix_segment', 'transition_matrix', ['portfolio_segment'])
    op.create_index('ix_transition_matrix_calibration', 'transition_matrix', ['calibration_date'])
    
    # Create rating_history table
    op.create_table('rating_history',
        sa.Column('history_id', sa.String(50), nullable=False),
        sa.Column('customer_id', sa.String(50), nullable=False),
        sa.Column('rating', sa.String(20), nullable=False),
        sa.Column('rating_date', sa.Date(), nullable=False),
        sa.Column('rating_agency', sa.String(50), nullable=True),  # INTERNAL, EXTERNAL
        sa.Column('rating_notch_change', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.customer_id'], ),
        sa.PrimaryKeyConstraint('history_id')
    )
    op.create_index('ix_rating_history_customer', 'rating_history', ['customer_id'])
    op.create_index('ix_rating_history_date', 'rating_history', ['rating_date'])
    
    # Add PD term structure fields to ecl_calculation
    op.add_column('ecl_calculation', sa.Column('pd_curve', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('ecl_calculation', sa.Column('pd_source', sa.String(50), nullable=True))  # TRANSITION_MATRIX, SCORECARD, PARAMETER
    
    # ========================================
    # TASK 32: Behavioral Scorecard PD
    # ========================================
    
    # Create behavioral_scorecard table
    op.create_table('behavioral_scorecard',
        sa.Column('scorecard_id', sa.String(50), nullable=False),
        sa.Column('product_type', sa.String(50), nullable=False),
        sa.Column('score_min', sa.Integer(), nullable=False),
        sa.Column('score_max', sa.Integer(), nullable=False),
        sa.Column('pd_estimate', sa.Numeric(8, 6), nullable=False),
        sa.Column('calibration_date', sa.Date(), nullable=False),
        sa.Column('gini_coefficient', sa.Numeric(6, 4), nullable=True),
        sa.Column('ks_statistic', sa.Numeric(6, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('scorecard_id')
    )
    op.create_index('ix_scorecard_product', 'behavioral_scorecard', ['product_type'])
    
    # Create customer_score table
    op.create_table('customer_score',
        sa.Column('score_id', sa.String(50), nullable=False),
        sa.Column('customer_id', sa.String(50), nullable=False),
        sa.Column('scorecard_id', sa.String(50), nullable=False),
        sa.Column('score_value', sa.Integer(), nullable=False),
        sa.Column('score_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.customer_id'], ),
        sa.ForeignKeyConstraint(['scorecard_id'], ['behavioral_scorecard.scorecard_id'], ),
        sa.PrimaryKeyConstraint('score_id')
    )
    op.create_index('ix_customer_score_customer', 'customer_score', ['customer_id'])
    
    # ========================================
    # TASK 33: Macro Variable Integration
    # ========================================
    
    # Enhance macro_scenario table with Uganda-specific variables
    op.add_column('macro_scenario', sa.Column('scenario_type', sa.String(20), nullable=True))  # BASELINE, OPTIMISTIC, DOWNTURN
    op.add_column('macro_scenario', sa.Column('forecast_quarter', sa.String(10), nullable=True))  # 2026-Q1
    op.add_column('macro_scenario', sa.Column('central_bank_rate', sa.Numeric(6, 4), nullable=True))
    op.add_column('macro_scenario', sa.Column('coffee_price_usd_lb', sa.Numeric(8, 4), nullable=True))
    op.add_column('macro_scenario', sa.Column('oil_price_usd_bbl', sa.Numeric(8, 4), nullable=True))
    op.add_column('macro_scenario', sa.Column('commercial_lending_rate', sa.Numeric(6, 4), nullable=True))
    
    # Create macro_regression_model table
    op.create_table('macro_regression_model',
        sa.Column('model_id', sa.String(50), nullable=False),
        sa.Column('dependent_variable', sa.String(20), nullable=False),  # PD, LGD
        sa.Column('coefficients', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('r_squared', sa.Numeric(6, 4), nullable=True),
        sa.Column('calibration_date', sa.Date(), nullable=False),
        sa.Column('portfolio_segment', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('model_id')
    )
    
    # ========================================
    # TASK 34: Facility-Level LGD
    # ========================================
    
    # Enhance collateral table
    op.add_column('collateral', sa.Column('forced_sale_value', sa.Numeric(18, 2), nullable=True))
    op.add_column('collateral', sa.Column('disposal_cost_pct', sa.Numeric(5, 2), nullable=True))
    op.add_column('collateral', sa.Column('revaluation_frequency_months', sa.Integer(), nullable=True))
    op.add_column('collateral', sa.Column('last_revaluation_date', sa.Date(), nullable=True))
    op.add_column('collateral', sa.Column('next_revaluation_date', sa.Date(), nullable=True))
    
    # Update collateral_type enum to include all CFO types
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'RESIDENTIAL_PROPERTY'")
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'COMMERCIAL_PROPERTY'")
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'MOTOR_VEHICLE'")
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'GOVERNMENT_SECURITIES'")
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'CASH_DEPOSIT'")
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'LISTED_EQUITIES'")
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'AGRICULTURAL_LAND'")
    op.execute("ALTER TYPE collateraltype ADD VALUE IF NOT EXISTS 'UNSECURED'")
    
    # Create collateral_haircut_config table
    op.create_table('collateral_haircut_config',
        sa.Column('config_id', sa.String(50), nullable=False),
        sa.Column('collateral_type', sa.String(50), nullable=False),
        sa.Column('standard_haircut_pct', sa.Numeric(5, 2), nullable=False),
        sa.Column('stressed_haircut_pct', sa.Numeric(5, 2), nullable=False),
        sa.Column('revaluation_frequency_months', sa.Integer(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('config_id')
    )
    
    # Create workout_recovery table for historical LGD data
    op.create_table('workout_recovery',
        sa.Column('recovery_id', sa.String(50), nullable=False),
        sa.Column('instrument_id', sa.String(50), nullable=False),
        sa.Column('default_date', sa.Date(), nullable=False),
        sa.Column('recovery_date', sa.Date(), nullable=True),
        sa.Column('exposure_at_default', sa.Numeric(18, 2), nullable=False),
        sa.Column('recovery_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('direct_costs', sa.Numeric(18, 2), nullable=True),
        sa.Column('time_to_recovery_months', sa.Integer(), nullable=True),
        sa.Column('realized_lgd', sa.Numeric(8, 6), nullable=True),
        sa.Column('product_type', sa.String(50), nullable=True),
        sa.Column('collateral_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['instrument_id'], ['financial_instrument.instrument_id'], ),
        sa.PrimaryKeyConstraint('recovery_id')
    )
    op.create_index('ix_workout_recovery_instrument', 'workout_recovery', ['instrument_id'])
    
    # Add facility-level LGD fields to ecl_calculation
    op.add_column('ecl_calculation', sa.Column('lgd_components', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('ecl_calculation', sa.Column('cure_rate', sa.Numeric(6, 4), nullable=True))
    
    # ========================================
    # TASK 35: Off-Balance Sheet EAD
    # ========================================
    
    # Add off-balance sheet fields to financial_instrument
    op.add_column('financial_instrument', sa.Column('undrawn_commitment_amount', sa.Numeric(18, 2), nullable=True))
    op.add_column('financial_instrument', sa.Column('facility_type', sa.String(50), nullable=True))
    op.add_column('financial_instrument', sa.Column('credit_conversion_factor', sa.Numeric(6, 4), nullable=True))
    op.add_column('financial_instrument', sa.Column('is_off_balance_sheet', sa.Boolean(), default=False))
    
    # Create ccf_config table
    op.create_table('ccf_config',
        sa.Column('config_id', sa.String(50), nullable=False),
        sa.Column('facility_type', sa.String(50), nullable=False),
        sa.Column('default_ccf', sa.Numeric(6, 4), nullable=False),
        sa.Column('calibration_source', sa.String(100), nullable=True),
        sa.Column('calibration_date', sa.Date(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('config_id')
    )
    
    # ========================================
    # TASK 36: Authentication & RBAC
    # ========================================
    
    # Create user table
    op.create_table('user',
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('account_locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index('ix_user_username', 'user', ['username'])
    op.create_index('ix_user_email', 'user', ['email'])
    
    # Create role table
    op.create_table('role',
        sa.Column('role_id', sa.String(50), nullable=False),
        sa.Column('role_name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('role_id')
    )
    
    # Create permission table
    op.create_table('permission',
        sa.Column('permission_id', sa.String(50), nullable=False),
        sa.Column('permission_name', sa.String(100), nullable=False, unique=True),
        sa.Column('resource', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('permission_id')
    )
    
    # Create user_role table
    op.create_table('user_role',
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('role_id', sa.String(50), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('assigned_by', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['role.role_id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    
    # Create role_permission table
    op.create_table('role_permission',
        sa.Column('role_id', sa.String(50), nullable=False),
        sa.Column('permission_id', sa.String(50), nullable=False),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.role_id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.permission_id'], ),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    
    # Create approval_workflow table
    op.create_table('approval_workflow',
        sa.Column('workflow_id', sa.String(50), nullable=False),
        sa.Column('workflow_type', sa.String(50), nullable=False),
        sa.Column('request_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('requester_id', sa.String(50), nullable=False),
        sa.Column('request_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('approver_id', sa.String(50), nullable=True),
        sa.Column('approval_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # PENDING, APPROVED, REJECTED
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['requester_id'], ['user.user_id'], ),
        sa.ForeignKeyConstraint(['approver_id'], ['user.user_id'], ),
        sa.PrimaryKeyConstraint('workflow_id')
    )
    op.create_index('ix_approval_workflow_status', 'approval_workflow', ['status'])
    op.create_index('ix_approval_workflow_type', 'approval_workflow', ['workflow_type'])
    
    # Create user_activity_log table
    op.create_table('user_activity_log',
        sa.Column('log_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('activity_description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('request_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
        sa.PrimaryKeyConstraint('log_id')
    )
    op.create_index('ix_user_activity_log_user', 'user_activity_log', ['user_id'])
    op.create_index('ix_user_activity_log_timestamp', 'user_activity_log', ['timestamp'])
    op.create_index('ix_user_activity_log_type', 'user_activity_log', ['activity_type'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('user_activity_log')
    op.drop_table('approval_workflow')
    op.drop_table('role_permission')
    op.drop_table('user_role')
    op.drop_table('permission')
    op.drop_table('role')
    op.drop_table('user')
    op.drop_table('ccf_config')
    op.drop_table('workout_recovery')
    op.drop_table('collateral_haircut_config')
    op.drop_table('macro_regression_model')
    op.drop_table('customer_score')
    op.drop_table('behavioral_scorecard')
    op.drop_table('rating_history')
    op.drop_table('transition_matrix')
    op.drop_table('staging_override')
    
    # Drop columns
    op.drop_column('financial_instrument', 'is_off_balance_sheet')
    op.drop_column('financial_instrument', 'credit_conversion_factor')
    op.drop_column('financial_instrument', 'facility_type')
    op.drop_column('financial_instrument', 'undrawn_commitment_amount')
    op.drop_column('ecl_calculation', 'cure_rate')
    op.drop_column('ecl_calculation', 'lgd_components')
    op.drop_column('collateral', 'next_revaluation_date')
    op.drop_column('collateral', 'last_revaluation_date')
    op.drop_column('collateral', 'revaluation_frequency_months')
    op.drop_column('collateral', 'disposal_cost_pct')
    op.drop_column('collateral', 'forced_sale_value')
    op.drop_column('macro_scenario', 'commercial_lending_rate')
    op.drop_column('macro_scenario', 'oil_price_usd_bbl')
    op.drop_column('macro_scenario', 'coffee_price_usd_lb')
    op.drop_column('macro_scenario', 'central_bank_rate')
    op.drop_column('macro_scenario', 'forecast_quarter')
    op.drop_column('macro_scenario', 'scenario_type')
    op.drop_column('ecl_calculation', 'pd_source')
    op.drop_column('ecl_calculation', 'pd_curve')
    op.drop_column('stage_transition', 'qualitative_indicators')
    op.drop_column('stage_transition', 'trigger_details')
    op.drop_column('customer', 'sector_risk_rating')
    op.drop_column('financial_instrument', 'forbearance_date')
    op.drop_column('financial_instrument', 'forbearance_granted')
    op.drop_column('financial_instrument', 'restructuring_date')
    op.drop_column('financial_instrument', 'is_restructured')
    op.drop_column('financial_instrument', 'watchlist_status')
