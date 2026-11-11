
import random
from collections import defaultdict
from datetime import date
from decimal import Decimal

from config import RANDOM_SEED, AS_OF_DATE
from src.models.entities import DelinquencySnapshot


def generate_delinquency_snapshots(db, loans, installments):
    rng = random.Random(RANDOM_SEED + 5)
    reference_date = date.fromisoformat(AS_OF_DATE)

    # Group installments by loan once for efficient lookup.
    installments_by_loan = defaultdict(list)

    for item in installments:
        installments_by_loan[item.loan_id].append(item)

    snapshots = []

    for loan in loans:
        loan_installments = installments_by_loan[loan.loan_id]

        overdue_installments = [
            item for item in loan_installments
            if item.due_date < reference_date
            and item.due_amount > item.paid_amount
        ]

        arrears = sum(
            (
                item.due_amount - item.paid_amount
                for item in overdue_installments
            ),
            Decimal("0.00"),
        )

        if overdue_installments:
            oldest_due_date = min(
                item.due_date for item in overdue_installments
            )
            dpd = (reference_date - oldest_due_date).days
        else:
            dpd = 0

        if dpd == 0:
            risk = "LOW"
        elif dpd <= 30:
            risk = "MEDIUM"
        elif dpd <= 60:
            risk = "HIGH"
        else:
            risk = "CRITICAL"

        snapshot = DelinquencySnapshot(
            snapshot_id=f"SNAP-{loan.loan_id}-{reference_date:%Y%m%d}",
            loan_id=loan.loan_id,
            snapshot_date=reference_date,
            days_past_due=dpd,
            arrears_amount=arrears,
            risk_category=risk,
            hardship_flag=rng.random() < 0.08,
            dispute_flag=rng.random() < 0.05,
        )

        snapshots.append(snapshot)

    db.add_all(snapshots)
    db.commit()

    print(
        f"SUCCESS: Generated {len(snapshots)} delinquency snapshots."
    )

    return snapshots
