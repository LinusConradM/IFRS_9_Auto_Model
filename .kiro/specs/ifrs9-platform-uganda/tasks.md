# Implementation Plan: IFRS 9 Automation Platform for Uganda

## Overview

This implementation plan covers the development of a comprehensive IFRS 9 automation platform for commercial banks in Uganda. The platform uses a modular monolithic architecture with Python 3.11+/FastAPI backend, PostgreSQL database, Redis caching, and RabbitMQ messaging. The implementation follows an incremental approach, building core infrastructure first, then implementing the 7 core modules (Data Import, Classification, Staging Engine, ECL Engine, Measurement, Reporting, Audit Trail), followed by API endpoints, frontend, and comprehensive testing including 40 property-based tests.

## Tasks

- [x] 1. Project setup and infrastructure foundation
  - [x] 1.1 Initialize Python project structure with FastAPI
    - Create directory structure: src/, tests/, docs/, scripts/, config/
    - Set up pyproject.toml with dependencies: FastAPI, SQLAlchemy, Pydantic, Alembic, pytest, Hypothesis
    - Configure Python 3.11+ virtual environment
    - Set up .gitignore for Python projects
    - _Requirements: 24.1, 24.2_
  
  - [x] 1.2 Configure Docker and Docker Compose for development
    - Create Dockerfile for FastAPI application
    - Create Dockerfile for worker service
    - Create docker-compose.yml with services: api, worker, postgres, redis, rabbitmq, minio
    - Configure environment variables and secrets management
    - _Requirements: 24.3, 24.4_
  
  - [x] 1.3 Set up database infrastructure with PostgreSQL
    - Configure PostgreSQL 15+ connection with SQLAlchemy
    - Set up Alembic for database migrations
    - Create initial migration structure
    - Configure connection pooling and transaction management
    - _Requirements: 24.1_
  
  - [x] 1.4 Set up Redis caching layer
    - Configure Redis connection with redis-py
    - Implement cache utility functions (get, set, delete, expire)
    - Set up Redis Sentinel configuration for HA (production)
    - _Requirements: 24.1_

  - [x] 1.5 Set up RabbitMQ message queue
    - Configure RabbitMQ connection with pika library
    - Create queue definitions for ECL calculations
    - Implement message publisher and consumer utilities
    - Configure dead letter exchange for failed messages
    - _Requirements: 24.1_
  
  - [x] 1.6 Set up MinIO object storage
    - Configure MinIO client for document storage
    - Create buckets for reports and audit documents
    - Implement file upload/download utilities
    - Configure server-side encryption
    - _Requirements: 24.1_
  
  - [x] 1.7 Configure logging and monitoring infrastructure
    - Set up structured logging with Python logging module
    - Configure log levels and formatters (JSON format)
    - Implement correlation ID tracking for request tracing
    - Set up Prometheus metrics endpoints
    - _Requirements: 24.5_

- [-] 2. Database schema implementation
  - [x] 2.1 Create core entity models with SQLAlchemy
    - Implement FinancialInstrument model with all fields
    - Implement Customer model
    - Implement ECLCalculation model
    - Implement StageTransition model
    - Implement ParameterSet model
    - Implement MacroScenario model
    - Implement Collateral model
    - Implement AuditEntry model
    - Configure relationships and foreign keys
    - _Requirements: 6.1, 6.2, 6.3, 7.1, 8.1, 11.7, 23.1_
  
  - [x] 2.2 Create database indexes for performance
    - Create indexes on financial_instrument (customer_id, current_stage, status, days_past_due)
    - Create indexes on ecl_calculation (instrument_id, reporting_date)
    - Create indexes on stage_transition (instrument_id, transition_date)
    - Create indexes on audit_entry (timestamp, entity_type, entity_id, user_id)
    - Create indexes on parameter_set (parameter_type, effective_date)
    - _Requirements: 24.2_

  - [x] 2.3 Create Pydantic schemas for API validation
    - Create request/response schemas for all entities
    - Implement validation rules (required fields, ranges, formats)
    - Create enum types (InstrumentType, Classification, Stage, etc.)
    - _Requirements: 16.1, 16.2, 16.3_
  
  - [x] 2.4 Create database migration scripts
    - Generate Alembic migration for all tables
    - Add migration for indexes
    - Add migration for constraints and foreign keys
    - Test migration up/down operations
    - _Requirements: 24.2_

- [ ] 3. Authentication and authorization system
  - [ ] 3.1 Implement OAuth 2.0 + JWT authentication
    - Create User model with password hashing (bcrypt)
    - Implement login endpoint with JWT token generation
    - Implement token refresh endpoint
    - Implement logout endpoint (token blacklisting)
    - Configure token expiry (1 hour access, 7 days refresh)
    - _Requirements: 15.1, 15.2, 25.4_
  
  - [ ]* 3.2 Write unit tests for authentication
    - Test successful login with valid credentials
    - Test login failure with invalid credentials
    - Test token refresh flow
    - Test token expiry handling
    - Test logout and token blacklisting
    - _Requirements: 15.1_
  
  - [ ] 3.3 Implement role-based access control (RBAC)
    - Create Role model (Administrator, Risk Manager, Accountant, Auditor, Viewer, Data Steward)
    - Create Permission model and role-permission mappings
    - Implement authorization decorators for API endpoints
    - Implement resource-level permission checks
    - _Requirements: 15.3, 15.4_

  - [ ]* 3.4 Write property test for authentication requirement
    - **Property 34: Authentication Requirement**
    - **Validates: Requirements 15.1**
    - Test that any API request without valid authentication is rejected
    - _Requirements: 15.1_
  
  - [ ]* 3.5 Write property test for authorization enforcement
    - **Property 35: Authorization Enforcement**
    - **Validates: Requirements 15.3, 15.4**
    - Test that any action requiring specific permissions is blocked without proper role
    - _Requirements: 15.3, 15.4_
  
  - [ ]* 3.6 Write property test for password complexity
    - **Property 36: Password Complexity**
    - **Validates: Requirements 15.6**
    - Test that all passwords meet complexity requirements (12+ chars, mixed case, numbers, special chars)
    - _Requirements: 15.6_

- [ ] 4. Audit trail system implementation
  - [x] 4.1 Implement audit trail service
    - Create AuditTrailService class with logging methods
    - Implement log_classification, log_staging, log_ecl_calculation methods
    - Implement log_parameter_change, log_user_action methods
    - Generate SHA-256 hash for audit entry integrity
    - Capture user context (user_id, IP address, session_id)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [x] 4.2 Implement audit trail query API
    - Create query_audit_trail method with filtering
    - Implement generate_audit_report method
    - Support filtering by entity type, entity ID, user, date range
    - _Requirements: 11.7_
  
  - [ ]* 4.3 Write property test for comprehensive audit trail
    - **Property 29: Comprehensive Audit Trail**
    - **Validates: Requirements 1.4, 2.6, 5.5, 6.7, 7.5, 8.6, 9.7, 11.1-11.5, 13.6, 15.5, 20.6, 22.4, 25.5**
    - Test that all system actions create corresponding audit entries
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 4.4 Write property test for audit trail immutability
    - **Property 30: Audit Trail Immutability**
    - **Validates: Requirements 11.8**
    - Test that audit entries cannot be modified or hard deleted once created
    - _Requirements: 11.8_
  
  - [ ]* 4.5 Write property test for audit trail retention
    - **Property 31: Audit Trail Retention**
    - **Validates: Requirements 11.6**
    - Test that audit entries are retained for minimum 7 years
    - _Requirements: 11.6_

- [ ] 5. Data import module implementation
  - [x] 5.1 Implement data import service core
    - Create DataImportService class
    - Implement import_loan_portfolio method (CSV/JSON parsing)
    - Implement import_customer_data method
    - Implement import_macro_data method
    - Support multiple data sources (file upload, SFTP, API)
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 5.2 Implement data validation engine
    - Create ValidationService class
    - Implement required field validation
    - Implement data type validation (numeric ranges, date formats)
    - Implement date sequence validation (origination < maturity)
    - Implement referential integrity checks (customer exists for loan)
    - Generate detailed validation reports
    - _Requirements: 6.4, 16.1, 16.2, 16.3, 16.6_
  
  - [x] 5.3 Implement duplicate detection
    - Create duplicate detection logic based on instrument_id
    - Flag duplicates in validation report
    - _Requirements: 16.4_
  
  - [x] 5.4 Implement import approval workflow
    - Create import staging area for pending imports
    - Implement approve_import and reject_import methods
    - Only commit data to main tables after approval
    - _Requirements: 6.5_

  - [ ]* 5.5 Write property test for data import validation
    - **Property 14: Data Import Validation**
    - **Validates: Requirements 6.4, 16.1, 16.2, 16.3, 16.6**
    - Test that all imports validate completeness, data types, formats, and referential integrity
    - _Requirements: 6.4, 16.1, 16.2, 16.3, 16.6_
  
  - [ ]* 5.6 Write property test for validation failure rejection
    - **Property 15: Validation Failure Rejection**
    - **Validates: Requirements 6.5, 16.5**
    - Test that failed validations reject import and generate error report
    - _Requirements: 6.5, 16.5_
  
  - [ ]* 5.7 Write property test for duplicate detection
    - **Property 16: Duplicate Detection**
    - **Validates: Requirements 16.4**
    - Test that duplicate records are identified based on unique identifiers
    - _Requirements: 16.4_
  
  - [ ]* 5.8 Write unit tests for data import
    - Test CSV file parsing with valid data
    - Test JSON file parsing with valid data
    - Test import with missing required fields
    - Test import with invalid data types
    - Test import with out-of-range values
    - Test import approval and rejection workflow
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Classification module implementation
  - [x] 6.1 Implement classification service
    - Create ClassificationService class
    - Implement classify_instrument method
    - Implement evaluate_business_model method
    - Implement evaluate_sppi_test method
    - Implement reclassify_instrument method
    - Store classification rationale in audit trail
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 6.2 Implement business model test logic
    - Evaluate business model based on instrument characteristics
    - Support HOLD_TO_COLLECT, HOLD_TO_COLLECT_AND_SELL, OTHER
    - Document business model determination rationale
    - _Requirements: 1.1_
  
  - [x] 6.3 Implement SPPI test logic
    - Evaluate cash flow characteristics (solely payments of principal and interest)
    - Identify non-SPPI features (equity conversion, commodity-linked returns)
    - Return pass/fail result with rationale
    - _Requirements: 1.2_
  
  - [x] 6.4 Implement classification decision logic
    - Apply classification rules based on business model and SPPI results
    - HOLD_TO_COLLECT + SPPI pass → Amortized Cost
    - HOLD_TO_COLLECT_AND_SELL + SPPI pass → FVOCI
    - SPPI fail → FVTPL
    - OTHER business model → FVTPL
    - _Requirements: 1.3, 1.5_
  
  - [ ]* 6.5 Write property test for classification completeness
    - **Property 1: Classification Completeness**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - Test that all instruments are evaluated and classified into exactly one category
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ]* 6.6 Write property test for SPPI test failure classification
    - **Property 2: SPPI Test Failure Classification**
    - **Validates: Requirements 1.5**
    - Test that SPPI test failure always results in FVTPL classification
    - _Requirements: 1.5_
  
  - [ ]* 6.7 Write unit tests for classification
    - Test classification of standard term loan (Amortized Cost)
    - Test classification of convertible bond (FVTPL)
    - Test classification of equity-linked instrument (FVTPL)
    - Test reclassification workflow
    - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [x] 7. Staging engine implementation
  - [x] 7.1 Implement staging service core
    - Create StagingService class
    - Implement determine_stage method
    - Implement evaluate_sicr method
    - Implement check_credit_impaired method
    - Implement get_stage_transitions method
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 7.2 Implement SICR detection logic
    - Implement quantitative indicators (PD increase threshold, absolute PD threshold)
    - Implement DPD > 30 days backstop indicator
    - Implement qualitative indicators (forbearance, watchlist, covenant breaches)
    - Return SICRResult with identified indicators
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [x] 7.3 Implement credit impairment detection
    - Check DPD > 90 days criterion
    - Check objective evidence of impairment
    - Return boolean result with rationale
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 7.4 Implement stage transition logic
    - Stage 1 → Stage 2 on SICR detection
    - Stage 2 → Stage 1 on SICR reversal
    - Stage 1/2 → Stage 3 on credit impairment
    - Stage 3 → Stage 2 on cure (no longer impaired but SICR present)
    - Stage 3 → Stage 1 on full cure (rare)
    - Record all transitions in stage_transition table
    - _Requirements: 2.3, 2.4, 2.5_
  
  - [x] 7.5 Implement configurable staging rules
    - Load SICR thresholds from parameter_set table
    - Support bank-specific PD increase thresholds
    - Support bank-specific absolute PD thresholds
    - Allow configuration of qualitative indicators
    - _Requirements: 3.1, 3.2, 20.1, 20.2_

  - [ ]* 7.6 Write property test for stage assignment completeness
    - **Property 3: Stage Assignment Completeness**
    - **Validates: Requirements 2.1**
    - Test that every instrument is assigned to exactly one stage at any time
    - _Requirements: 2.1_
  
  - [ ]* 7.7 Write property test for initial recognition stage
    - **Property 4: Initial Recognition Stage**
    - **Validates: Requirements 2.2**
    - Test that all instruments at initial recognition are assigned to Stage 1
    - _Requirements: 2.2_
  
  - [ ]* 7.8 Write property test for SICR stage transition
    - **Property 5: SICR Stage Transition**
    - **Validates: Requirements 2.3**
    - Test that Stage 1 instruments with SICR transition to Stage 2
    - _Requirements: 2.3_
  
  - [ ]* 7.9 Write property test for credit impairment stage transition
    - **Property 6: Credit Impairment Stage Transition**
    - **Validates: Requirements 2.4**
    - Test that credit-impaired instruments transition to Stage 3
    - _Requirements: 2.4_
  
  - [ ]* 7.10 Write property test for SICR reversal stage transition
    - **Property 7: SICR Reversal Stage Transition**
    - **Validates: Requirements 2.5**
    - Test that Stage 2 instruments without SICR revert to Stage 1
    - _Requirements: 2.5_
  
  - [ ]* 7.11 Write property test for DPD SICR threshold
    - **Property 8: Days Past Due SICR Threshold**
    - **Validates: Requirements 3.3**
    - Test that DPD > 30 days triggers SICR detection
    - _Requirements: 3.3_
  
  - [ ]* 7.12 Write property test for DPD credit impairment threshold
    - **Property 9: Days Past Due Credit Impairment Threshold**
    - **Validates: Requirements 5.1**
    - Test that DPD > 90 days triggers credit impairment classification
    - _Requirements: 5.1_

  - [ ]* 7.13 Write unit tests for staging engine
    - Test initial stage assignment (Stage 1)
    - Test SICR detection with DPD = 31 days
    - Test SICR detection with PD increase > threshold
    - Test credit impairment with DPD = 91 days
    - Test stage transition from Stage 1 to Stage 2
    - Test stage transition from Stage 2 to Stage 3
    - Test stage reversal from Stage 2 to Stage 1
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.3, 5.1_

- [ ] 8. Checkpoint - Core modules foundation complete
  - Ensure all tests pass, ask the user if questions arise.

- [-] 9. ECL calculation engine implementation
  - [x] 9.1 Implement ECL calculation service core
    - Create ECLCalculationService class
    - Implement calculate_ecl method (main entry point)
    - Implement calculate_12m_ecl method for Stage 1
    - Implement calculate_lifetime_ecl method for Stage 2/3
    - Implement recalculate_portfolio method for bulk calculations
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 9.2 Implement ECL formula calculation
    - Implement ECL = Σ(PD_t × LGD_t × EAD_t × DF_t) formula
    - Support 12-month horizon for Stage 1
    - Support lifetime horizon for Stage 2/3
    - Calculate discount factors using effective interest rate
    - _Requirements: 4.4_
  
  - [x] 9.3 Implement parameter lookup service
    - Create ParameterService class
    - Implement get_pd, get_lgd, get_ead methods
    - Support segmentation by customer type, product type, credit rating
    - Cache parameters in Redis for performance
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 9.4 Implement macroeconomic scenario integration
    - Create MacroScenarioService class
    - Implement apply_macro_scenarios method
    - Adjust PD/LGD based on macro indicators (GDP, inflation, unemployment)
    - Support base, upside, downside scenarios
    - _Requirements: 8.1, 8.2_
  
  - [x] 9.5 Implement scenario weighting
    - Calculate probability-weighted ECL across scenarios
    - Formula: Weighted ECL = Σ(weight_i × ECL_i)
    - Validate that scenario weights sum to 1.0
    - _Requirements: 4.7, 8.3_
  
  - [ ] 9.6 Implement collective ECL calculation
    - Group instruments by segment (customer type, product type, rating)
    - Calculate collective ECL for homogeneous portfolios
    - Support both individual and collective assessment
    - _Requirements: 4.5, 4.6_
  
  - [ ] 9.7 Implement asynchronous calculation with RabbitMQ
    - Create ECL calculation worker
    - Publish calculation jobs to RabbitMQ queue
    - Consume jobs in worker process
    - Update calculation status (pending, in_progress, completed, failed)
    - Support priority queue for urgent recalculations
    - _Requirements: 24.1_
  
  - [ ]* 9.8 Write property test for stage-ECL type consistency
    - **Property 10: Stage-ECL Type Consistency**
    - **Validates: Requirements 4.1, 4.2, 4.3, 17.3, 17.4**
    - Test that Stage 1 uses 12-month ECL, Stage 2/3 use Lifetime ECL
    - _Requirements: 4.1, 4.2, 4.3, 17.3, 17.4_
  
  - [ ]* 9.9 Write property test for ECL calculation formula
    - **Property 11: ECL Calculation Formula**
    - **Validates: Requirements 4.4**
    - Test that ECL = Σ(PD_t × LGD_t × EAD_t × DF_t) for all calculations
    - _Requirements: 4.4_

  - [ ]* 9.10 Write property test for scenario weighting
    - **Property 12: Scenario Weighting**
    - **Validates: Requirements 4.7, 8.3**
    - Test that weighted ECL equals sum of (weight × scenario_ECL) and weights sum to 1.0
    - _Requirements: 4.7, 8.3_
  
  - [ ]* 9.11 Write property test for parameter recalculation trigger
    - **Property 17: Parameter Recalculation Trigger**
    - **Validates: Requirements 7.6, 8.5, 23.5**
    - Test that ECL is recalculated when PD, LGD, EAD, scenarios, or collateral values change
    - _Requirements: 7.6, 8.5, 23.5_
  
  - [ ]* 9.12 Write unit tests for ECL calculation
    - Test 12-month ECL calculation for Stage 1 instrument
    - Test lifetime ECL calculation for Stage 2 instrument
    - Test scenario weighting with 3 scenarios
    - Test collective ECL calculation for portfolio segment
    - Test ECL calculation with missing parameters (error handling)
    - Test asynchronous calculation job submission and completion
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ] 10. Collateral and LGD calculation
  - [ ] 10.1 Implement collateral valuation service
    - Create CollateralService class
    - Implement get_collateral_value method
    - Apply haircut percentage to collateral value
    - Calculate net realizable value
    - _Requirements: 23.1, 23.3_
  
  - [ ] 10.2 Integrate collateral into LGD calculation
    - Adjust LGD based on collateral net realizable value
    - Formula: Adjusted LGD = max(0, (EAD - Collateral NRV) / EAD)
    - Support multiple collateral items per instrument
    - _Requirements: 23.2, 23.4_

  - [ ]* 10.3 Write property test for collateral LGD incorporation
    - **Property 26: Collateral LGD Incorporation**
    - **Validates: Requirements 23.2, 23.4**
    - Test that LGD calculation incorporates collateral net realizable value
    - _Requirements: 23.2, 23.4_
  
  - [ ]* 10.4 Write unit tests for collateral
    - Test collateral valuation with haircut
    - Test LGD adjustment with single collateral
    - Test LGD adjustment with multiple collateral items
    - Test LGD calculation with zero collateral
    - _Requirements: 23.1, 23.2, 23.3, 23.4_

- [ ] 11. POCI (Purchased or Originated Credit Impaired) handling
  - [ ] 11.1 Implement POCI identification and flagging
    - Add is_poci flag to FinancialInstrument model
    - Identify POCI assets at origination
    - _Requirements: 21.1_
  
  - [ ] 11.2 Implement credit-adjusted EIR calculation for POCI
    - Calculate credit-adjusted effective interest rate at initial recognition
    - Incorporate expected credit losses into EIR calculation
    - Store credit-adjusted EIR in instrument record
    - _Requirements: 21.2_
  
  - [ ] 11.3 Implement POCI stage immutability
    - Prevent stage transitions for POCI instruments
    - POCI instruments remain in their initial stage
    - _Requirements: 21.3, 21.4_
  
  - [ ] 11.4 Implement POCI interest revenue calculation
    - Calculate interest revenue using credit-adjusted EIR
    - Apply to net carrying amount
    - _Requirements: 21.5_

  - [ ]* 11.5 Write property test for POCI stage immutability
    - **Property 21: POCI Stage Immutability**
    - **Validates: Requirements 21.4**
    - Test that POCI instruments do not undergo stage transitions
    - _Requirements: 21.4_
  
  - [ ]* 11.6 Write property test for POCI credit-adjusted EIR
    - **Property 22: POCI Credit-Adjusted EIR**
    - **Validates: Requirements 21.2, 21.5**
    - Test that POCI assets use credit-adjusted EIR for interest revenue
    - _Requirements: 21.2, 21.5_
  
  - [ ]* 11.7 Write unit tests for POCI
    - Test POCI identification at origination
    - Test credit-adjusted EIR calculation
    - Test that POCI instruments don't transition stages
    - Test POCI interest revenue calculation
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

- [ ] 12. Modification and derecognition handling
  - [ ] 12.1 Implement modification detection and 10% test
    - Create ModificationService class
    - Implement 10% cash flow test (compare PV of original vs modified cash flows)
    - Determine if modification is substantial (>10% difference)
    - _Requirements: 22.1, 22.5_
  
  - [ ] 12.2 Implement substantial modification treatment
    - Derecognize original asset
    - Recognize new asset at fair value
    - Calculate and record gain/loss on derecognition
    - _Requirements: 22.2_
  
  - [ ] 12.3 Implement non-substantial modification treatment
    - Recalculate gross carrying amount
    - Calculate modification gain/loss
    - Recognize gain/loss in profit or loss
    - Update instrument record with modification details
    - _Requirements: 22.3_

  - [ ]* 12.4 Write property test for modification derecognition test
    - **Property 23: Modification Derecognition Test**
    - **Validates: Requirements 22.5**
    - Test that 10% cash flow test is applied to all modifications
    - _Requirements: 22.5_
  
  - [ ]* 12.5 Write property test for substantial modification treatment
    - **Property 24: Substantial Modification Treatment**
    - **Validates: Requirements 22.2**
    - Test that substantial modifications result in derecognition and new asset recognition
    - _Requirements: 22.2_
  
  - [ ]* 12.6 Write property test for non-substantial modification treatment
    - **Property 25: Non-Substantial Modification Treatment**
    - **Validates: Requirements 22.3**
    - Test that non-substantial modifications recalculate gross carrying amount
    - _Requirements: 22.3_
  
  - [ ]* 12.7 Write unit tests for modification
    - Test 10% cash flow test with substantial modification (>10%)
    - Test 10% cash flow test with non-substantial modification (<10%)
    - Test derecognition and new asset recognition
    - Test gross carrying amount recalculation
    - Test modification gain/loss calculation
    - _Requirements: 22.1, 22.2, 22.3, 22.5_

- [ ] 13. Measurement module implementation
  - [ ] 13.1 Implement measurement service
    - Create MeasurementService class
    - Implement measure_instrument method
    - Implement calculate_amortized_cost method
    - Implement calculate_interest_revenue method
    - Implement calculate_effective_interest_rate method
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [ ] 13.2 Implement amortized cost measurement
    - Calculate gross carrying amount (PV of future cash flows at EIR)
    - Subtract ECL to get amortized cost
    - Formula: Amortized Cost = Gross Carrying Amount - ECL
    - _Requirements: 12.1, 12.4_
  
  - [ ] 13.3 Implement interest revenue calculation
    - Stage 1/2: Interest Revenue = Gross Carrying Amount × EIR
    - Stage 3: Interest Revenue = Net Carrying Amount × EIR
    - Support monthly, quarterly, annual calculation periods
    - _Requirements: 12.5, 12.6_
  
  - [ ] 13.4 Implement effective interest rate calculation
    - Calculate EIR using IRR method on cash flows
    - Support standard EIR for non-POCI assets
    - Support credit-adjusted EIR for POCI assets
    - _Requirements: 12.4, 21.2_
  
  - [ ]* 13.5 Write property test for measurement classification consistency
    - **Property 18: Measurement Classification Consistency**
    - **Validates: Requirements 12.1, 12.2, 12.3**
    - Test that measurement basis matches classification (AC at amortized cost, FVOCI at fair value, FVTPL at fair value)
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [ ]* 13.6 Write property test for credit-impaired interest calculation
    - **Property 13: Credit-Impaired Interest Calculation**
    - **Validates: Requirements 5.4, 12.6**
    - Test that Stage 3 instruments calculate interest on net carrying amount
    - _Requirements: 5.4, 12.6_
  
  - [ ]* 13.7 Write unit tests for measurement
    - Test amortized cost calculation
    - Test interest revenue for Stage 1 instrument
    - Test interest revenue for Stage 3 instrument (on net carrying amount)
    - Test EIR calculation
    - Test measurement for FVOCI instrument
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 14. Write-off and recovery handling
  - [ ] 14.1 Implement write-off service
    - Create WriteOffService class
    - Implement write_off_instrument method
    - Update instrument status to WRITTEN_OFF
    - Record write-off amount and date
    - Continue tracking written-off amount for recovery monitoring
    - _Requirements: 14.1, 14.2_
  
  - [ ] 14.2 Implement recovery tracking
    - Implement record_recovery method
    - Record recovery amount and date
    - Update cumulative recovery amount
    - _Requirements: 14.3_
  
  - [ ]* 14.3 Write property test for write-off tracking continuity
    - **Property 27: Write-Off Tracking Continuity**
    - **Validates: Requirements 14.2**
    - Test that written-off instruments continue to be tracked for recovery
    - _Requirements: 14.2_
  
  - [ ]* 14.4 Write property test for recovery recording
    - **Property 28: Recovery Recording**
    - **Validates: Requirements 14.3**
    - Test that recoveries are recorded with amount and date
    - _Requirements: 14.3_
  
  - [ ]* 14.5 Write unit tests for write-off and recovery
    - Test write-off of Stage 3 instrument
    - Test recovery recording
    - Test cumulative recovery tracking
    - _Requirements: 14.1, 14.2, 14.3_

- [ ] 15. Checkpoint - Core calculation engines complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Reporting engine implementation
  - [ ] 16.1 Implement reporting service core
    - Create ReportingService class
    - Implement generate_regulatory_report method
    - Implement generate_management_report method
    - Implement generate_dashboard method
    - Implement export_report method (PDF, Excel, CSV)
    - _Requirements: 9.1, 9.2, 9.3, 9.6_
  
  - [ ] 16.2 Implement ECL reconciliation report
    - Calculate opening ECL balance
    - Calculate ECL movements (new originations, derecognitions, stage transitions, parameter changes)
    - Calculate closing ECL balance
    - Validate that opening + movements = closing
    - _Requirements: 17.1, 17.2, 9.5_
  
  - [ ] 16.3 Implement regulatory reports for Bank of Uganda
    - Monthly Impairment Provision Report (ECL by stage, coverage ratios)
    - Quarterly Credit Risk Report (stage transitions, SICR analysis)
    - Annual IFRS 9 Disclosure Report (complete ECL reconciliation, methodology)
    - Ensure format compliance with Bank of Uganda specifications
    - _Requirements: 9.1, 9.4_
  
  - [ ] 16.4 Implement management dashboard
    - Real-time portfolio metrics (total exposure, ECL, coverage ratio)
    - ECL trends over time
    - Stage distribution visualization
    - Concentration analysis by sector, customer type
    - Alert notifications for high-risk instruments
    - _Requirements: 9.3_
  
  - [ ] 16.5 Implement PDF report generation
    - Use ReportLab for PDF generation
    - Create report templates for regulatory reports
    - Include charts and tables
    - Store generated reports in MinIO
    - _Requirements: 9.6_

  - [ ] 16.6 Implement report scheduling
    - Create scheduled jobs for monthly, quarterly, annual reports
    - Use APScheduler for job scheduling
    - Send email notifications when reports are ready
    - _Requirements: 9.7_
  
  - [ ]* 16.7 Write property test for ECL reconciliation
    - **Property 19: ECL Reconciliation**
    - **Validates: Requirements 17.1**
    - Test that total portfolio ECL equals sum of individual instrument ECL
    - _Requirements: 17.1_
  
  - [ ]* 16.8 Write property test for ECL movement reconciliation
    - **Property 20: ECL Movement Reconciliation**
    - **Validates: Requirements 17.2**
    - Test that ECL change is fully explained by movements
    - _Requirements: 17.2_
  
  - [ ]* 16.9 Write property test for report format compliance
    - **Property 39: Report Format Compliance**
    - **Validates: Requirements 9.4**
    - Test that regulatory reports conform to Bank of Uganda specifications
    - _Requirements: 9.4_
  
  - [ ]* 16.10 Write property test for ECL reconciliation in reports
    - **Property 40: ECL Reconciliation in Reports**
    - **Validates: Requirements 9.5**
    - Test that reports include opening to closing ECL reconciliation
    - _Requirements: 9.5_
  
  - [ ]* 16.11 Write unit tests for reporting
    - Test monthly impairment provision report generation
    - Test ECL reconciliation calculation
    - Test PDF export
    - Test Excel export
    - Test dashboard data generation
    - Test report scheduling
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [ ] 17. Historical data and retention implementation
  - [ ] 17.1 Implement historical data snapshot service
    - Create HistoricalDataService class
    - Implement create_snapshot method for reporting dates
    - Store complete portfolio state (instruments, ECL, stages, parameters)
    - _Requirements: 18.1, 18.2, 18.3_
  
  - [ ] 17.2 Implement historical data query service
    - Implement query_historical_data method
    - Support querying by reporting date
    - Return complete snapshot for specified date
    - _Requirements: 18.4_
  
  - [ ] 17.3 Implement data retention policy enforcement
    - Implement 7-year retention for historical snapshots
    - Implement 7-year retention for audit entries
    - Implement 7-year retention for ECL calculations
    - Create automated archival process for old data
    - _Requirements: 18.5, 11.6_
  
  - [ ]* 17.4 Write property test for historical data retention
    - **Property 32: Historical Data Retention**
    - **Validates: Requirements 18.1, 18.2, 18.3, 18.5**
    - Test that complete snapshots are retained for minimum 7 years
    - _Requirements: 18.1, 18.2, 18.3, 18.5_
  
  - [ ]* 17.5 Write property test for historical data queryability
    - **Property 33: Historical Data Queryability**
    - **Validates: Requirements 18.4**
    - Test that historical data can be queried for any prior period within retention
    - _Requirements: 18.4_
  
  - [ ]* 17.6 Write unit tests for historical data
    - Test snapshot creation for reporting date
    - Test historical data query
    - Test data retention policy enforcement
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 18. Configuration management implementation
  - [ ] 18.1 Implement configuration service
    - Create ConfigurationService class
    - Implement get_config, set_config methods
    - Support SICR thresholds configuration
    - Support staging rules configuration
    - Support segmentation criteria configuration
    - _Requirements: 20.1, 20.2, 20.3, 20.4_
  
  - [ ] 18.2 Implement configuration validation
    - Validate internal consistency of configuration changes
    - Validate that SICR thresholds are positive
    - Validate that scenario weights sum to 1.0
    - Prevent invalid configuration from being applied
    - _Requirements: 20.5_
  
  - [ ] 18.3 Implement configuration versioning
    - Track configuration changes with version numbers
    - Store configuration history
    - Support rollback to previous configuration
    - _Requirements: 20.6_
  
  - [ ]* 18.4 Write property test for configuration validation
    - **Property 37: Configuration Validation**
    - **Validates: Requirements 20.5**
    - Test that configuration changes are validated for internal consistency
    - _Requirements: 20.5_
  
  - [ ]* 18.5 Write unit tests for configuration
    - Test configuration retrieval
    - Test configuration update
    - Test configuration validation (valid and invalid cases)
    - Test configuration versioning
    - Test configuration rollback
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_

- [ ] 19. REST API endpoints implementation
  - [ ] 19.1 Implement authentication endpoints
    - POST /api/v1/auth/login (username/password, return JWT)
    - POST /api/v1/auth/refresh (refresh token, return new JWT)
    - POST /api/v1/auth/logout (blacklist token)
    - GET /api/v1/auth/me (get current user info)
    - _Requirements: 15.1, 15.2, 25.1_
  
  - [x] 19.2 Implement data import endpoints
    - POST /api/v1/imports/loan-portfolio (upload CSV/JSON)
    - POST /api/v1/imports/customer-data
    - POST /api/v1/imports/macro-scenarios
    - GET /api/v1/imports/{import_id} (get import status)
    - GET /api/v1/imports/{import_id}/validation-report
    - POST /api/v1/imports/{import_id}/approve
    - POST /api/v1/imports/{import_id}/reject
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 25.1_
  
  - [x] 19.3 Implement financial instrument endpoints
    - GET /api/v1/instruments (list with pagination, filtering)
    - GET /api/v1/instruments/{instrument_id}
    - POST /api/v1/instruments (create new instrument)
    - PUT /api/v1/instruments/{instrument_id} (update instrument)
    - DELETE /api/v1/instruments/{instrument_id} (soft delete)
    - GET /api/v1/instruments/{instrument_id}/history
    - GET /api/v1/instruments/{instrument_id}/ecl-calculations
    - GET /api/v1/instruments/{instrument_id}/stage-transitions
    - _Requirements: 25.1_
  
  - [x] 19.4 Implement classification endpoints
    - POST /api/v1/classification/classify (classify single instrument)
    - POST /api/v1/classification/reclassify/{instrument_id}
    - GET /api/v1/classification/{instrument_id}/rationale
    - _Requirements: 1.1, 1.2, 1.3, 25.1_

  - [x] 19.5 Implement staging endpoints
    - POST /api/v1/staging/determine-stage (determine stage for instrument)
    - POST /api/v1/staging/evaluate-sicr/{instrument_id}
    - GET /api/v1/staging/transitions (list stage transitions with filters)
    - POST /api/v1/staging/manual-override/{instrument_id} (manual stage override)
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 25.1_
  
  - [x] 19.6 Implement ECL calculation endpoints
    - POST /api/v1/ecl/calculate (calculate ECL for single instrument)
    - POST /api/v1/ecl/calculate-portfolio (bulk calculation)
    - GET /api/v1/ecl/calculations (list calculations with filters)
    - GET /api/v1/ecl/calculations/{calculation_id}
    - POST /api/v1/ecl/recalculate/{instrument_id}
    - GET /api/v1/ecl/jobs/{job_id} (get async job status)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 25.1_
  
  - [x] 19.7 Implement parameter endpoints
    - GET /api/v1/parameters (list parameters with filters)
    - GET /api/v1/parameters/{parameter_id}
    - POST /api/v1/parameters (create new parameter)
    - PUT /api/v1/parameters/{parameter_id} (update parameter)
    - GET /api/v1/parameters/history/{parameter_id}
    - POST /api/v1/parameters/{parameter_id}/approve
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 25.1_
  
  - [x] 19.8 Implement macroeconomic scenario endpoints
    - GET /api/v1/scenarios (list scenarios)
    - GET /api/v1/scenarios/{scenario_id}
    - POST /api/v1/scenarios (create scenario)
    - PUT /api/v1/scenarios/{scenario_id} (update scenario)
    - DELETE /api/v1/scenarios/{scenario_id}
    - _Requirements: 8.1, 8.2, 8.3, 25.1_

  - [x] 19.9 Implement reporting endpoints
    - GET /api/v1/reports/regulatory/{report_type} (generate regulatory report)
    - GET /api/v1/reports/management/{report_type} (generate management report)
    - POST /api/v1/reports/custom (generate custom report)
    - GET /api/v1/reports/{report_id} (get report details)
    - GET /api/v1/reports/{report_id}/export/{format} (export as PDF/Excel/CSV)
    - POST /api/v1/reports/schedule (schedule recurring report)
    - _Requirements: 9.1, 9.2, 9.3, 9.6, 9.7, 25.1_
  
  - [x] 19.10 Implement audit trail endpoints
    - GET /api/v1/audit/entries (list audit entries with filters)
    - GET /api/v1/audit/entries/{audit_id}
    - GET /api/v1/audit/instrument/{instrument_id} (audit trail for instrument)
    - GET /api/v1/audit/user/{user_id} (audit trail for user)
    - POST /api/v1/audit/search (advanced search)
    - _Requirements: 11.7, 25.1_
  
  - [ ] 19.11 Implement API error handling and validation
    - Create standardized error response format
    - Implement request validation with Pydantic
    - Implement error codes (VALIDATION_ERROR, AUTHENTICATION_FAILED, etc.)
    - Add request_id to all responses for tracing
    - _Requirements: 25.2_
  
  - [ ] 19.12 Implement API rate limiting
    - Configure rate limits (100 req/min standard, 10 req/min calculations)
    - Return 429 status code when limit exceeded
    - Include rate limit headers in responses
    - _Requirements: 25.3_
  
  - [ ]* 19.13 Write property test for API authentication
    - **Property 38: API Authentication**
    - **Validates: Requirements 25.4**
    - Test that all API requests require valid authentication
    - _Requirements: 25.4_

  - [ ]* 19.14 Write integration tests for API endpoints
    - Test authentication flow (login, refresh, logout)
    - Test data import flow (upload, validate, approve)
    - Test classification API
    - Test staging API
    - Test ECL calculation API (sync and async)
    - Test parameter management API
    - Test reporting API
    - Test audit trail API
    - Test error responses and status codes
    - Test rate limiting
    - _Requirements: 25.1, 25.2, 25.3, 25.4_

- [ ] 20. Checkpoint - API layer complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 21. Frontend implementation with React and TypeScript
  - [ ] 21.1 Set up React project with TypeScript
    - Initialize React 18+ project with Vite
    - Configure TypeScript with strict mode
    - Set up routing with React Router
    - Configure API client with Axios
    - Set up state management (React Context or Redux)
    - _Requirements: 24.1_
  
  - [ ] 21.2 Implement authentication UI
    - Create login page with username/password form
    - Implement JWT token storage (localStorage)
    - Implement automatic token refresh
    - Create protected route wrapper
    - Implement logout functionality
    - _Requirements: 15.1, 15.2_
  
  - [ ] 21.3 Implement dashboard page
    - Display portfolio summary metrics (total exposure, ECL, coverage ratio)
    - Display ECL trends chart
    - Display stage distribution pie chart
    - Display concentration analysis by sector
    - Display alert notifications for high-risk instruments
    - Auto-refresh data every 5 minutes
    - _Requirements: 9.3, 10.1_

  - [ ] 21.4 Implement instrument management UI
    - Create instrument list page with pagination and filtering
    - Create instrument detail page showing classification, stage, ECL
    - Display ECL calculation history
    - Display stage transition history
    - Support instrument search by ID, customer, status
    - _Requirements: 10.2_
  
  - [ ] 21.5 Implement data import UI
    - Create file upload page for loan portfolio, customer data
    - Display import progress and validation results
    - Show validation errors with details
    - Implement approve/reject buttons for imports
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 10.3_
  
  - [ ] 21.6 Implement parameter management UI
    - Create parameter list page with filters
    - Create parameter edit form
    - Display parameter history
    - Implement parameter approval workflow
    - _Requirements: 7.5, 10.4_
  
  - [ ] 21.7 Implement reporting UI
    - Create report selection page (regulatory, management, custom)
    - Display report generation progress
    - Implement report preview
    - Implement export buttons (PDF, Excel, CSV)
    - Create report scheduling interface
    - _Requirements: 9.1, 9.2, 9.3, 9.6, 9.7, 10.5_
  
  - [ ] 21.8 Implement audit trail UI
    - Create audit log viewer with filtering
    - Display audit entry details
    - Support search by entity, user, date range
    - Display before/after states for changes
    - _Requirements: 11.7, 10.6_

  - [ ] 21.9 Implement user management UI (admin only)
    - Create user list page
    - Create user creation/edit form
    - Implement role assignment
    - Display user activity log
    - _Requirements: 15.3, 15.4, 10.7_
  
  - [ ] 21.10 Implement responsive design and accessibility
    - Ensure mobile-responsive layout
    - Implement ARIA labels for screen readers
    - Ensure keyboard navigation support
    - Test with accessibility tools
    - _Requirements: 10.8_

- [ ] 22. Security hardening
  - [ ] 22.1 Implement TLS/SSL configuration
    - Configure TLS 1.3 for all API communications
    - Generate SSL certificates (Let's Encrypt for production)
    - Configure HTTPS redirect
    - _Requirements: 19.1_
  
  - [ ] 22.2 Implement data encryption at rest
    - Configure PostgreSQL Transparent Data Encryption (TDE)
    - Configure MinIO server-side encryption
    - Implement field-level encryption for PII (customer names, addresses)
    - Set up key management (HashiCorp Vault or AWS KMS)
    - _Requirements: 19.2, 19.3_
  
  - [ ] 22.3 Implement security monitoring
    - Track failed login attempts (lock after 5 failures)
    - Detect unusual access patterns
    - Log all privileged actions
    - Monitor API rate limit violations
    - Monitor data export activities
    - _Requirements: 19.4_

  - [ ] 22.4 Implement security incident response
    - Create automated alerts for security events
    - Implement automatic account lockout
    - Implement IP blocking for repeated violations
    - Create incident logging and reporting
    - _Requirements: 19.5_
  
  - [ ]* 22.5 Write security tests
    - Test authentication with invalid credentials
    - Test authorization with insufficient permissions
    - Test SQL injection prevention
    - Test XSS prevention
    - Test CSRF protection
    - Test rate limiting enforcement
    - _Requirements: 15.1, 15.3, 25.3_

- [ ] 23. Performance optimization
  - [ ] 23.1 Implement database query optimization
    - Add database indexes (already defined in schema)
    - Optimize N+1 query problems with eager loading
    - Implement query result caching in Redis
    - Configure connection pooling (min 10, max 50 connections)
    - _Requirements: 24.2_
  
  - [ ] 23.2 Implement Redis caching strategy
    - Cache parameter lookups (TTL: 1 hour)
    - Cache ECL calculation results (TTL: 24 hours)
    - Cache dashboard metrics (TTL: 5 minutes)
    - Implement cache invalidation on data updates
    - _Requirements: 24.1_
  
  - [ ] 23.3 Implement asynchronous processing optimization
    - Configure RabbitMQ worker pool (4 workers)
    - Implement priority queues (urgent recalculations first)
    - Implement job batching for bulk calculations
    - Add progress tracking for long-running jobs
    - _Requirements: 24.1_

  - [ ]* 23.4 Write performance tests
    - Test ECL calculation for 100,000 instrument portfolio (target: < 2 hours)
    - Test report generation time (target: < 15 minutes)
    - Test concurrent user load (target: 50 users)
    - Test API response times (target: < 500ms for standard endpoints)
    - _Requirements: 24.2_

- [ ] 24. Monitoring and observability
  - [ ] 24.1 Implement Prometheus metrics
    - Expose /metrics endpoint
    - Track API request count and latency
    - Track ECL calculation duration
    - Track database query performance
    - Track cache hit/miss rates
    - Track queue depth and processing time
    - _Requirements: 24.5_
  
  - [ ] 24.2 Set up Grafana dashboards
    - Create system health dashboard (CPU, memory, disk)
    - Create application metrics dashboard (API latency, throughput)
    - Create business metrics dashboard (ECL trends, portfolio metrics)
    - Create alert rules for critical metrics
    - _Requirements: 24.5_
  
  - [ ] 24.3 Implement structured logging
    - Configure JSON log format
    - Add correlation IDs to all logs
    - Implement log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Configure log rotation (daily, 90-day retention)
    - Set up centralized log aggregation
    - _Requirements: 24.5_
  
  - [ ] 24.4 Implement health check endpoints
    - Create /health endpoint (basic liveness check)
    - Create /health/ready endpoint (readiness check with DB, Redis, RabbitMQ)
    - Return detailed status for each dependency
    - _Requirements: 24.5_

- [ ] 25. Deployment configuration
  - [ ] 25.1 Create production Docker Compose configuration
    - Configure production environment variables
    - Set up PostgreSQL with replication
    - Set up Redis Sentinel cluster
    - Set up RabbitMQ cluster
    - Configure resource limits (CPU, memory)
    - _Requirements: 24.3, 24.4_
  
  - [ ] 25.2 Create Kubernetes deployment manifests (optional, future scaling)
    - Create Deployment manifests for API, worker, frontend
    - Create Service manifests
    - Create ConfigMap and Secret manifests
    - Create PersistentVolumeClaim for database
    - Create Ingress for external access
    - _Requirements: 24.4_
  
  - [ ] 25.3 Implement backup and restore procedures
    - Create automated database backup script (daily full, 6-hour incremental)
    - Create backup verification script (weekly restore test)
    - Configure off-site backup to cloud storage
    - Document restore procedures
    - _Requirements: 24.6_
  
  - [ ] 25.4 Create deployment documentation
    - Document system requirements
    - Document installation steps
    - Document configuration options
    - Document backup/restore procedures
    - Document troubleshooting guide
    - _Requirements: 24.7_

- [ ] 26. CI/CD pipeline setup
  - [ ] 26.1 Configure CI pipeline
    - Set up GitLab CI / GitHub Actions
    - Run linting (pylint, black, mypy)
    - Run unit tests with pytest
    - Run property-based tests with Hypothesis (100 iterations)
    - Generate code coverage report (target: > 80%)
    - Build Docker images
    - Push images to container registry
    - _Requirements: 24.8_

  - [ ] 26.2 Configure CD pipeline
    - Deploy to development environment (automatic on main branch)
    - Run smoke tests in development
    - Deploy to UAT environment (manual approval)
    - Run UAT test suite
    - Deploy to production (manual approval with change control)
    - Run production smoke tests
    - Monitor for errors post-deployment
    - _Requirements: 24.8_
  
  - [ ]* 26.3 Write smoke tests
    - Test API health endpoint
    - Test authentication flow
    - Test basic CRUD operations
    - Test ECL calculation (small portfolio)
    - Test report generation
    - _Requirements: 24.8_

- [ ] 27. User acceptance testing (UAT) preparation
  - [ ] 27.1 Create UAT test data
    - Generate synthetic loan portfolio (1,000 instruments)
    - Create test customers across all segments
    - Create test macroeconomic scenarios
    - Create test parameters (PD, LGD, EAD)
    - _Requirements: 26.1_
  
  - [ ] 27.2 Create UAT test scenarios
    - Import loan portfolio and validate
    - Review classification results
    - Review staging results
    - Verify ECL calculations against manual calculations
    - Generate regulatory reports
    - Test audit trail queries
    - Test user access controls
    - _Requirements: 26.2_
  
  - [ ] 27.3 Create UAT documentation
    - Create user guide for each role
    - Create test scenario scripts
    - Create expected results documentation
    - Create issue reporting template
    - _Requirements: 26.3_

- [ ] 28. Final integration and system testing
  - [ ]* 28.1 Run complete integration test suite
    - Test end-to-end workflow: import → classify → stage → calculate ECL → report
    - Test data flow between all modules
    - Test error handling and recovery
    - Test concurrent operations
    - Test transaction rollback scenarios
    - _Requirements: All requirements_
  
  - [ ]* 28.2 Run all property-based tests
    - Execute all 40 property tests with 100 iterations each
    - Verify all properties pass
    - Document any edge cases discovered
    - _Requirements: All requirements_
  
  - [ ]* 28.3 Run performance and load tests
    - Test with 100,000 instrument portfolio
    - Measure ECL calculation time
    - Measure report generation time
    - Test with 50 concurrent users
    - Identify and resolve bottlenecks
    - _Requirements: 24.2_
  
  - [ ]* 28.4 Run security testing
    - Perform penetration testing
    - Test authentication and authorization
    - Test data encryption
    - Test audit trail integrity
    - Verify compliance with security requirements
    - _Requirements: 15.1, 15.3, 19.1, 19.2, 19.3_
  
  - [ ] 28.5 Verify regulatory compliance
    - Verify all Bank of Uganda report formats
    - Verify 7-year data retention
    - Verify audit trail completeness
    - Verify data residency (Uganda)
    - _Requirements: 9.4, 11.6, 18.5, 27.1_

- [ ] 29. Final checkpoint - System complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (40 properties total)
- Unit tests validate specific examples, edge cases, and error conditions
- Integration tests validate end-to-end workflows and module interactions
- The implementation follows an incremental approach: infrastructure → core modules → API → frontend → testing
- All 7 core modules are implemented: Data Import, Classification, Staging Engine, ECL Engine, Measurement, Reporting, Audit Trail
- Security, performance, and monitoring are integrated throughout
- The platform uses Python 3.11+ with FastAPI, PostgreSQL, Redis, RabbitMQ, and MinIO
- Deployment supports Docker Compose (initial) and Kubernetes (future scaling)
- UAT preparation ensures bank stakeholders can validate the system before production deployment

## Implementation Approach

The task list follows a bottom-up implementation strategy:

1. **Foundation (Tasks 1-4)**: Set up infrastructure, database, authentication, and audit trail
2. **Core Modules (Tasks 5-14)**: Implement the 7 core business logic modules with comprehensive testing
3. **Reporting & Data Management (Tasks 15-18)**: Implement reporting, historical data, and configuration
4. **API Layer (Tasks 19-20)**: Expose all functionality via REST API with security and validation
5. **Frontend (Task 21)**: Build user interface for all user roles
6. **Hardening (Tasks 22-24)**: Security, performance optimization, and monitoring
7. **Deployment (Tasks 25-26)**: Production deployment configuration and CI/CD
8. **Validation (Tasks 27-29)**: UAT preparation and final system testing

Each module includes property-based tests for universal correctness properties and unit tests for specific scenarios, ensuring comprehensive test coverage and regulatory compliance.
