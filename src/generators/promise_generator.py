
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from config import RANDOM_SEED, AS_OF_DATE
from src.models.entities import Loan, DelinquencySnapshot
from src.models.events import CollectionCase, PromiseToPay


def generate_promises(
    db: Session,
    cases: list[CollectionCase],
    loans: list[Loan],
    snapshots: list[DelinquencySnapshot],
):
    """Generate promises within each loan's outstanding arrears."""

    rng = random.Random(RANDOM_SEED + 20)
    reference_date = date.fromisoformat(AS_OF_DATE)

    snapshot_by_loan = {
        snapshot.loan_id: snapshot for snapshot in snapshots
    }

    promises = []

    for number, case in enumerate(cases, start=1):

        # Generate promises for approximately 30% of cases.
        if rng.random() >= 0.30:
            continue

        snapshot = snapshot_by_loan.get(case.loan_id)

        if snapshot is None or snapshot.arrears_amount <= Decimal("0.00"):
            continue

        arrears = snapshot.arrears_amount

        # Promise amount is between 25% and 100% of arrears.
        percentage = rng.choice([25, 50, 75, 100])

        promised_amount = (
            arrears * Decimal(percentage) / Decimal("100")
        ).quantize(Decimal("0.01"))

        if promised_amount <= Decimal("0.00"):
            continue

        promise = PromiseToPay(
            promise_id=f"PTP-{case.case_id}-001",
            case_id=case.case_id,
            promised_amount=promised_amount,
            promised_date=reference_date + timedelta(
                days=rng.randint(1, 14)
            ),
            promise_status=rng.choice(
                ["PENDING", "FULFILLED", "BROKEN"]
            ),
        )

        promises.append(promise)

    db.add_all(promises)
    db.commit()

    print(f"SUCCESS: Generated {len(promises)} promises.")

    return promises
