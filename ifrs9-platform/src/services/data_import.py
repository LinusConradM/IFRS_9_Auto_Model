"""Data import service for loan portfolio and customer data"""
import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid
from io import StringIO
from sqlalchemy.orm import Session

from src.db.models import (
    Customer, FinancialInstrument, ParameterSet, MacroScenario,
    InstrumentType, Classification, BusinessModel, Stage, InstrumentStatus, CustomerType
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ImportResult:
    """Result of data import operation"""
    def __init__(self, import_id: str, status: str, records_processed: int,
                 records_imported: int, records_failed: int, errors: List[Dict]):
        self.import_id = import_id
        self.status = status
        self.records_processed = records_processed
        self.records_imported = records_imported
        self.records_failed = records_failed
        self.errors = errors


class ValidationError:
    """Validation error for import record"""
    def __init__(self, row_number: int, field: str, error: str, value: Any = None):
        self.row_number = row_number
        self.field = field
        self.error = error
        self.value = value
    
    def to_dict(self) -> Dict:
        return {
            'row_number': self.row_number,
            'field': self.field,
            'error': self.error,
            'value': str(self.value) if self.value is not None else None
        }


class DataImportService:
    """Service for importing loan portfolio and customer data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def import_loan_portfolio(self, file_content: str, file_format: str = 'csv',
                             auto_approve: bool = False) -> ImportResult:
        """
        Import loan portfolio data from CSV or JSON file.
        
        Expected CSV columns:
        - instrument_id, customer_id, instrument_type, principal_amount,
          outstanding_balance, interest_rate, origination_date, maturity_date,
          days_past_due, is_poci, is_forbearance, is_watchlist
        
        Args:
            file_content: File content as string
            file_format: 'csv' or 'json'
            auto_approve: If True, import directly; if False, stage for approval
            
        Returns:
            ImportResult with import statistics
        """
        import_id = str(uuid.uuid4())
        logger.info(f"Starting loan portfolio import {import_id}, format={file_format}")
        
        # Parse file
        if file_format == 'csv':
            records = self._parse_csv(file_content)
        elif file_format == 'json':
            records = self._parse_json(file_content)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        # Validate and import records
        imported_count = 0
        failed_count = 0
        errors = []
        
        for idx, record in enumerate(records, start=1):
            try:
                # Validate record
                validation_errors = self._validate_instrument_record(record, idx)
                if validation_errors:
                    failed_count += 1
                    errors.extend([e.to_dict() for e in validation_errors])
                    continue
                
                # Check for duplicates
                existing = self.db.query(FinancialInstrument).filter(
                    FinancialInstrument.instrument_id == record['instrument_id']
                ).first()
                
                if existing:
                    failed_count += 1
                    errors.append({
                        'row_number': idx,
                        'field': 'instrument_id',
                        'error': 'Duplicate instrument_id',
                        'value': record['instrument_id']
                    })
                    continue
                
                # Get or create customer
                customer = self._get_or_create_customer(record)
                
                # Create instrument
                instrument = self._create_instrument(record, customer.id)
                
                if auto_approve:
                    self.db.add(instrument)
                    imported_count += 1
                else:
                    # TODO: Add to staging area for approval
                    imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing row {idx}: {e}")
                failed_count += 1
                errors.append({
                    'row_number': idx,
                    'field': 'general',
                    'error': str(e),
                    'value': None
                })
        
        if auto_approve:
            self.db.commit()
        
        status = 'completed' if failed_count == 0 else 'completed_with_errors'
        
        result = ImportResult(
            import_id=import_id,
            status=status,
            records_processed=len(records),
            records_imported=imported_count,
            records_failed=failed_count,
            errors=errors
        )
        
        logger.info(f"Import {import_id} completed: {imported_count} imported, {failed_count} failed")
        return result
    
    def import_customer_data(self, file_content: str, file_format: str = 'csv') -> ImportResult:
        """
        Import customer master data.
        
        Expected CSV columns:
        - customer_id, name, customer_type, sector, credit_rating,
          registration_date, country
        
        Args:
            file_content: File content as string
            file_format: 'csv' or 'json'
            
        Returns:
            ImportResult with import statistics
        """
        import_id = str(uuid.uuid4())
        logger.info(f"Starting customer data import {import_id}")
        
        # Parse file
        if file_format == 'csv':
            records = self._parse_csv(file_content)
        elif file_format == 'json':
            records = self._parse_json(file_content)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        imported_count = 0
        failed_count = 0
        errors = []
        
        for idx, record in enumerate(records, start=1):
            try:
                # Validate record
                validation_errors = self._validate_customer_record(record, idx)
                if validation_errors:
                    failed_count += 1
                    errors.extend([e.to_dict() for e in validation_errors])
                    continue
                
                # Check for duplicates
                existing = self.db.query(Customer).filter(
                    Customer.customer_id == record['customer_id']
                ).first()
                
                if existing:
                    # Update existing customer
                    existing.name = record['name']
                    existing.customer_type = CustomerType[record['customer_type']]
                    existing.sector = record.get('sector')
                    existing.credit_rating = record.get('credit_rating')
                    existing.country = record.get('country', 'Uganda')
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new customer
                    customer = Customer(
                        customer_id=record['customer_id'],
                        name=record['name'],
                        customer_type=CustomerType[record['customer_type']],
                        sector=record.get('sector'),
                        credit_rating=record.get('credit_rating'),
                        registration_date=self._parse_date(record.get('registration_date')),
                        country=record.get('country', 'Uganda'),
                        is_active=True
                    )
                    self.db.add(customer)
                
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing customer row {idx}: {e}")
                failed_count += 1
                errors.append({
                    'row_number': idx,
                    'field': 'general',
                    'error': str(e),
                    'value': None
                })
        
        self.db.commit()
        
        status = 'completed' if failed_count == 0 else 'completed_with_errors'
        
        result = ImportResult(
            import_id=import_id,
            status=status,
            records_processed=len(records),
            records_imported=imported_count,
            records_failed=failed_count,
            errors=errors
        )
        
        logger.info(f"Customer import {import_id} completed: {imported_count} imported, {failed_count} failed")
        return result
    
    def import_macro_data(self, file_content: str, file_format: str = 'csv') -> ImportResult:
        """
        Import macroeconomic scenario data.
        
        Expected CSV columns:
        - scenario_name, scenario_type, probability_weight, gdp_growth,
          inflation_rate, unemployment_rate, interest_rate, effective_date
        
        Args:
            file_content: File content as string
            file_format: 'csv' or 'json'
            
        Returns:
            ImportResult with import statistics
        """
        import_id = str(uuid.uuid4())
        logger.info(f"Starting macro scenario import {import_id}")
        
        # Parse file
        if file_format == 'csv':
            records = self._parse_csv(file_content)
        elif file_format == 'json':
            records = self._parse_json(file_content)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        imported_count = 0
        failed_count = 0
        errors = []
        
        for idx, record in enumerate(records, start=1):
            try:
                scenario = MacroScenario(
                    scenario_name=record['scenario_name'],
                    scenario_type=record['scenario_type'],
                    probability_weight=Decimal(str(record['probability_weight'])),
                    gdp_growth=Decimal(str(record.get('gdp_growth', 0))) if record.get('gdp_growth') else None,
                    inflation_rate=Decimal(str(record.get('inflation_rate', 0))) if record.get('inflation_rate') else None,
                    unemployment_rate=Decimal(str(record.get('unemployment_rate', 0))) if record.get('unemployment_rate') else None,
                    interest_rate=Decimal(str(record.get('interest_rate', 0))) if record.get('interest_rate') else None,
                    effective_date=self._parse_date(record['effective_date']),
                    is_active=True
                )
                
                self.db.add(scenario)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing macro scenario row {idx}: {e}")
                failed_count += 1
                errors.append({
                    'row_number': idx,
                    'field': 'general',
                    'error': str(e),
                    'value': None
                })
        
        self.db.commit()
        
        status = 'completed' if failed_count == 0 else 'completed_with_errors'
        
        result = ImportResult(
            import_id=import_id,
            status=status,
            records_processed=len(records),
            records_imported=imported_count,
            records_failed=failed_count,
            errors=errors
        )
        
        logger.info(f"Macro import {import_id} completed: {imported_count} imported, {failed_count} failed")
        return result
    
    def _parse_csv(self, content: str) -> List[Dict]:
        """Parse CSV content into list of dicts"""
        reader = csv.DictReader(StringIO(content))
        return list(reader)
    
    def _parse_json(self, content: str) -> List[Dict]:
        """Parse JSON content into list of dicts"""
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'records' in data:
            return data['records']
        else:
            raise ValueError("JSON must be array or object with 'records' key")
    
    def _validate_instrument_record(self, record: Dict, row_number: int) -> List[ValidationError]:
        """Validate financial instrument record"""
        errors = []
        
        # Required fields
        required_fields = [
            'instrument_id', 'customer_id', 'instrument_type',
            'principal_amount', 'outstanding_balance', 'interest_rate',
            'origination_date', 'maturity_date'
        ]
        
        for field in required_fields:
            if not record.get(field):
                errors.append(ValidationError(row_number, field, 'Required field missing'))
        
        # Validate instrument_type
        if record.get('instrument_type'):
            try:
                InstrumentType[record['instrument_type']]
            except KeyError:
                errors.append(ValidationError(
                    row_number, 'instrument_type',
                    f"Invalid instrument_type. Must be one of: {[e.name for e in InstrumentType]}",
                    record['instrument_type']
                ))
        
        # Validate numeric fields
        try:
            principal = Decimal(str(record.get('principal_amount', 0)))
            if principal <= 0:
                errors.append(ValidationError(row_number, 'principal_amount', 'Must be positive'))
        except:
            errors.append(ValidationError(row_number, 'principal_amount', 'Invalid numeric value'))
        
        try:
            outstanding = Decimal(str(record.get('outstanding_balance', 0)))
            if outstanding < 0:
                errors.append(ValidationError(row_number, 'outstanding_balance', 'Cannot be negative'))
        except:
            errors.append(ValidationError(row_number, 'outstanding_balance', 'Invalid numeric value'))
        
        # Validate dates
        try:
            orig_date = self._parse_date(record.get('origination_date'))
            mat_date = self._parse_date(record.get('maturity_date'))
            
            if orig_date and mat_date and orig_date >= mat_date:
                errors.append(ValidationError(
                    row_number, 'maturity_date',
                    'Maturity date must be after origination date'
                ))
        except:
            errors.append(ValidationError(row_number, 'dates', 'Invalid date format'))
        
        return errors
    
    def _validate_customer_record(self, record: Dict, row_number: int) -> List[ValidationError]:
        """Validate customer record"""
        errors = []
        
        # Required fields
        required_fields = ['customer_id', 'name', 'customer_type']
        
        for field in required_fields:
            if not record.get(field):
                errors.append(ValidationError(row_number, field, 'Required field missing'))
        
        # Validate customer_type
        if record.get('customer_type'):
            try:
                CustomerType[record['customer_type']]
            except KeyError:
                errors.append(ValidationError(
                    row_number, 'customer_type',
                    f"Invalid customer_type. Must be one of: {[e.name for e in CustomerType]}",
                    record['customer_type']
                ))
        
        return errors
    
    def _get_or_create_customer(self, record: Dict) -> Customer:
        """Get existing customer or create new one"""
        customer = self.db.query(Customer).filter(
            Customer.customer_id == record['customer_id']
        ).first()
        
        if not customer:
            customer = Customer(
                customer_id=record['customer_id'],
                name=record.get('customer_name', f"Customer {record['customer_id']}"),
                customer_type=CustomerType.RETAIL,  # Default
                country='Uganda',
                is_active=True
            )
            self.db.add(customer)
            self.db.flush()  # Get customer.id
        
        return customer
    
    def _create_instrument(self, record: Dict, customer_id: int) -> FinancialInstrument:
        """Create financial instrument from record"""
        instrument = FinancialInstrument(
            instrument_id=record['instrument_id'],
            customer_id=customer_id,
            instrument_type=InstrumentType[record['instrument_type']],
            classification=Classification.AMORTIZED_COST,  # Default, will be classified
            business_model=BusinessModel.HOLD_TO_COLLECT,  # Default
            sppi_test_passed=True,  # Default
            current_stage=Stage.STAGE_1,  # Default
            status=InstrumentStatus.ACTIVE,
            origination_date=self._parse_date(record['origination_date']),
            maturity_date=self._parse_date(record['maturity_date']),
            principal_amount=Decimal(str(record['principal_amount'])),
            outstanding_balance=Decimal(str(record['outstanding_balance'])),
            interest_rate=Decimal(str(record['interest_rate'])),
            days_past_due=int(record.get('days_past_due', 0)),
            is_poci=record.get('is_poci', 'false').lower() == 'true',
            is_forbearance=record.get('is_forbearance', 'false').lower() == 'true',
            is_watchlist=record.get('is_watchlist', 'false').lower() == 'true'
        )
        
        return instrument
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string in various formats"""
        if not date_str:
            return None
        
        # Try common date formats
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")
