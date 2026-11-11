
import argparse

from config import STARTER_LOAN_COUNT, FULL_LOAN_COUNT

from src.database import Base, engine, SessionLocal

from src.generators.customer_generator import generate_customers
from src.generators.account_generator import generate_accounts
from src.generators.loan_generator import generate_loans
from src.generators.installment_generator import generate_installments
from src.generators.delinquency_generator import (
    generate_delinquency_snapshots,
)
from src.generators.contact_preference_generator import (
    generate_contact_preferences,
)
from src.generators.collection_case_generator import (
    generate_collection_cases,
)
from src.generators.contact_attempt_generator import (
    generate_contact_attempts,
)
from src.generators.promise_generator import generate_promises
from src.generators.payment_generator import generate_payments


def run_pipeline(scale: str):
    """Generate the complete synthetic collections dataset."""

    loan_count = (
        STARTER_LOAN_COUNT
        if scale == "starter"
        else FULL_LOAN_COUNT
    )

    print("\n======================================")
    print(" YOTTAFLEX DATA GENERATION PIPELINE")
    print("======================================")
    print(f"Dataset scale: {scale}")
    print(f"Number of loans: {loan_count}")

    # Reset generated database for a clean run.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("\nSTEP 1: Generating customers...")
        customers = generate_customers(db, loan_count)

        print("\nSTEP 2: Generating accounts...")
        accounts = generate_accounts(db, customers)

        print("\nSTEP 3: Generating loans...")
        loans = generate_loans(db, accounts)

        print("\nSTEP 4: Generating installments...")
        installments = generate_installments(db, loans)

        print("\nSTEP 5: Generating delinquency snapshots...")
        snapshots = generate_delinquency_snapshots(
            db, loans, installments
        )

        print("\nSTEP 6: Generating contact preferences...")
        preferences = generate_contact_preferences(db, customers)

        print("\nSTEP 7: Generating collection cases...")
        cases = generate_collection_cases(db, loans, snapshots)

        print("\nSTEP 8: Generating contact attempts...")
        attempts = generate_contact_attempts(
            db, cases, loans, accounts, preferences
        )

        print("\nSTEP 9: Generating promises to pay...")
        promises = generate_promises(
            db, cases, loans, snapshots
        )

        print("\nSTEP 10: Generating payments...")
        payments = generate_payments(
            db, loans, installments, cases
        )

        print("\n======================================")
        print(" DATA GENERATION COMPLETED")
        print("======================================")
        print(f"Customers: {len(customers)}")
        print(f"Accounts: {len(accounts)}")
        print(f"Loans: {len(loans)}")
        print(f"Installments: {len(installments)}")
        print(f"Snapshots: {len(snapshots)}")
        print(f"Contact preferences: {len(preferences)}")
        print(f"Collection cases: {len(cases)}")
        print(f"Contact attempts: {len(attempts)}")
        print(f"Promises: {len(promises)}")
        print(f"Payments: {len(payments)}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YottaFlex synthetic data generator"
    )

    parser.add_argument(
        "--scale",
        choices=["starter", "full"],
        default="starter",
        help="Choose starter (100 loans) or full (10,000 loans)",
    )

    args = parser.parse_args()
    run_pipeline(args.scale)
