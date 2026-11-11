
import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from config import RANDOM_SEED, AS_OF_DATE
from src.models.entities import Account, Loan

random.seed(RANDOM_SEED)


def generate_loans(db: Session, accounts: list[Account]):
    """Generate one synthetic loan for each account."""

    loans = []
    reference_date = datetime.strptime(AS_OF_DATE, "%Y-%m-%d").date()

    for number, account in enumerate(accounts, start=1):

        principal = Decimal(
            str(random.randrange(30000, 300001, 5000))
        )

        start_date = reference_date - timedelta(
            days=random.randint(180, 730)
        )

        loan = Loan(
            loan_id=f"LOAN-2026-{number:06d}",
            account_id=account.account_id,
            principal_amount=principal,
            interest_rate=Decimal(
                str(random.choice([8.5, 9.5, 10.5, 12.0, 13.5, 15.0]))
            ),
            loan_status=random.choices(
                ["ACTIVE", "PAID_OFF", "CLOSED"],
                weights=[85, 10, 5],
                k=1
            )[0],
            start_date=start_date,
            end_date=start_date + timedelta(days=365),
        )

        loans.append(loan)

    db.add_all(loans)
    db.commit()

    print(f"SUCCESS: Generated {len(loans)} loans.")

    return loans
