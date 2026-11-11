
import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from config import RANDOM_SEED, AS_OF_DATE
from src.models.entities import Account, Customer

random.seed(RANDOM_SEED)


def generate_accounts(db: Session, customers: list[Customer]):
    """Generate one synthetic account for each customer."""

    accounts = []

    reference_date = datetime.strptime(AS_OF_DATE, "%Y-%m-%d").date()

    for number, customer in enumerate(customers, start=1):

        opened_date = reference_date - timedelta(
            days=random.randint(365, 1825)
        )

        account = Account(
            account_id=f"ACC-{number:06d}",
            customer_id=customer.customer_id,
            account_status=random.choices(
                ["ACTIVE", "CLOSED"],
                weights=[90, 10],
                k=1
            )[0],
            opened_date=opened_date,
        )

        accounts.append(account)

    db.add_all(accounts)
    db.commit()

    print(f"SUCCESS: Generated {len(accounts)} accounts.")

    return accounts
