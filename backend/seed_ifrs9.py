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
from db.models import LoanPortfolio, CollateralInformation, LoanBookVersion

from dateutil import parser as date_parser


def try_parse_date(value):
    try:
        return date_parser.parse(value).date() if value else None
    except Exception:
        return None


def load_dummy_loan_book(session, csv_path):
    version = LoanBookVersion(snapshot_data={})
    session.add(version)
    session.flush()

    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        # Normalize CSV headers to lowercase with no spaces
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]

        # Print actual headers for debugging
        print("🔍 CSV Headers:", reader.fieldnames)

        # Map CSV field → model field
        field_mapping = {
            "loan_id": "loan_id",
            "borrower_id": "borrower_id",
            "drawdown_date": "drawdown_date",
            "maturity_date": "maturity_date",
            "pd_12m": "pd_12m",
            "pd_lifetime": "pd_lifetime",
            "lgd": "lgd",
            "ead": "ead",
            "stage": "stage",
            "sicr_flag": "sicr_flag",
            "impairment_allowance": "impairment_allowance"
        }

        rows_loaded = 0

        for i, raw_row in enumerate(reader):
            # Normalize row keys
            row = {k.strip().lower(): v.strip() if isinstance(v, str) else v for k, v in raw_row.items()}

            # Remap field names
            mapped = {model_field: row.get(csv_field) for csv_field, model_field in field_mapping.items()}

            # Use loan_id from file, fallback to index if missing
            mapped["loan_id"] = mapped.get("loan_id") or str(i + 1)
            mapped["version_id"] = version.version_id

            # Validate required field
            if not mapped.get("borrower_id"):
                print(f"⚠️ Skipping row {i + 1}: Missing borrower_id")
                continue

            try:
                drawdown = try_parse_date(mapped.get("drawdown_date"))
                maturity = try_parse_date(mapped.get("maturity_date"))

                loan = LoanPortfolio(
                    loan_id=mapped["loan_id"],
                    borrower_id=mapped.get("borrower_id"),
                    drawdown_date=drawdown,
                    maturity_date=maturity,
                    pd_12m=mapped.get("pd_12m"),
                    pd_lifetime=mapped.get("pd_lifetime"),
                    lgd=mapped.get("lgd"),
                    ead=mapped.get("ead"),
                    sicr_flag=mapped.get("sicr_flag") in ("true", "True", "1", "yes", "Yes"),
                    stage=int(mapped.get("stage")) if mapped.get("stage") else None,
                    impairment_allowance=mapped.get("impairment_allowance"),
                    version_id=mapped["version_id"],
                )
                session.add(loan)
                rows_loaded += 1
                
                if row.get("collateral_type") or row.get("collateral_value") or row.get("guarantee_amount"):
                    appraisal = try_parse_date(row.get("appraisal_date"))
                    collateral = CollateralInformation(
                        loan_id=mapped["loan_id"],
                        collateral_type=row.get("collateral_type"),
                        value=row.get("collateral_value"),
                        appraisal_date=appraisal,
                        ltv=row.get("ltv"),
                        guarantee_amount=row.get("guarantee_amount"),
                    )
                    session.add(collateral)


            except Exception as e:
                print(f"❌ Error processing row {i + 1}: {e}")
                session.rollback()

    session.commit()
    print(f"✅ Loaded {rows_loaded} loan records into version {version.version_id}")


def main():
    parser = argparse.ArgumentParser(description='Seed IFRS9 dummy loan book data.')
    parser.add_argument('--csv', required=True, help='Path to CSV file with loan book data')
    args = parser.parse_args()
    csv_path = args.csv

    if not os.path.isfile(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        load_dummy_loan_book(session, csv_path)
    except IntegrityError as e:
        session.rollback()
        print(f"❌ IntegrityError loading data: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    main()
