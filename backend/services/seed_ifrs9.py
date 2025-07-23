import csv
import sys
from datetime import datetime

from core.database import SessionLocal, engine, Base
from models.loan_portfolio import LoanPortfolio


def seed_from_csv(csv_path: str) -> None:
    """Populate loan_portfolio table from a CSV file."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        loans = []
        for row in reader:
            loans.append(
                LoanPortfolio(
                    borrower_id=row['borrower_id'],
                    loan_id=row['loan_id'],
                    stage=int(row['stage']),
                    pd=float(row['pd']),
                    lgd=float(row['lgd']),
                    ead=float(row['ead']),
                    impairment=float(row['impairment']) if row.get('impairment') else None,
                    drawdown_date=datetime.strptime(row['drawdown_date'], '%Y-%m-%d').date(),
                    maturity_date=datetime.strptime(row['maturity_date'], '%Y-%m-%d').date(),
                    default_flag=row.get('default_flag', '').lower() in ('true', '1', 'yes'),
                )
            )
    session.bulk_save_objects(loans)
    session.commit()
    session.close()


def main() -> None:
    if len(sys.argv) != 2:
        print('Usage: python seed_ifrs9.py <path_to_csv>')
        sys.exit(1)
    seed_from_csv(sys.argv[1])


if __name__ == '__main__':
    main()