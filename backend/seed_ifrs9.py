"""
Seed the database with IFRS 9 dummy loan book data.
"""
import argparse
import csv
import os
import datetime

from sqlalchemy.exc import IntegrityError

from db.session import SessionLocal, engine, Base
from db.models import LoanPortfolio, CollateralInformation, LoanBookVersion


def load_dummy_loan_book(session, csv_path):
    version = LoanBookVersion(snapshot_data={})
    session.add(version)
    session.flush()
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            drawdown = datetime.date.fromisoformat(row.get('drawdown_date')) if row.get('drawdown_date') else None
            maturity = datetime.date.fromisoformat(row.get('maturity_date')) if row.get('maturity_date') else None
            loan = LoanPortfolio(
                loan_id=row.get('loan_id'),
                borrower_id=row.get('borrower_id'),
                drawdown_date=drawdown,
                maturity_date=maturity,
                pd_12m=row.get('pd_12m'),
                pd_lifetime=row.get('pd_lifetime'),
                lgd=row.get('lgd'),
                ead=row.get('ead'),
                sicr_flag=row.get('sicr_flag') in ('true', 'True', '1'),
                stage=int(row.get('stage')) if row.get('stage') else None,
                impairment_allowance=row.get('impairment_allowance'),
                version_id=version.version_id,
            )
            session.add(loan)
            if row.get('collateral_type'):
                appraisal = datetime.date.fromisoformat(row.get('appraisal_date')) if row.get('appraisal_date') else None
                collateral = CollateralInformation(
                    loan_id=row.get('loan_id'),
                    collateral_type=row.get('collateral_type'),
                    value=row.get('collateral_value'),
                    appraisal_date=appraisal,
                    ltv=row.get('ltv'),
                    guarantee_amount=row.get('guarantee_amount'),
                )
                session.add(collateral)
    session.commit()
    print(f"Loaded dummy loan book into version {version.version_id}")


def main():
    parser = argparse.ArgumentParser(description='Seed IFRS9 dummy loan book data.')
    parser.add_argument('--csv', required=True, help='Path to CSV file with loan book data')
    args = parser.parse_args()
    csv_path = args.csv
    if not os.path.isfile(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        load_dummy_loan_book(session, csv_path)
    except IntegrityError as e:
        session.rollback()
        print(f"Error loading data: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    main()