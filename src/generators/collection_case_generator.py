
from decimal import Decimal

from sqlalchemy.orm import Session

from src.models.entities import Loan, DelinquencySnapshot
from src.models.events import CollectionCase


def generate_collection_cases(
    db: Session,
    loans: list[Loan],
    snapshots: list[DelinquencySnapshot],
):
    """Create collection cases only for eligible overdue loans."""

    snapshot_by_loan = {
        snapshot.loan_id: snapshot
        for snapshot in snapshots
    }

    eligible_loans = []

    for loan in loans:
        snapshot = snapshot_by_loan.get(loan.loan_id)

        if (
            loan.loan_status == "ACTIVE"
            and snapshot is not None
            and snapshot.arrears_amount > Decimal("0.00")
            and not snapshot.dispute_flag
        ):
            eligible_loans.append((loan, snapshot))

    cases = []

    for number, (loan, snapshot) in enumerate(
        eligible_loans, start=1
    ):
        dpd_score = min(snapshot.days_past_due / 90 * 60, 60)

        arrears_score = min(
            float(snapshot.arrears_amount) / 100000 * 25,
            25,
        )

        hardship_penalty = 10 if snapshot.hardship_flag else 0

        priority_score = max(
            0,
            min(
                100,
                dpd_score
                + arrears_score
                + 15
                - hardship_penalty,
            ),
        )

        case = CollectionCase(
            case_id=f"COL-2026-{number:06d}",
            loan_id=loan.loan_id,
            case_status="OPEN",
            priority_score=Decimal(str(round(priority_score, 2))),
        )

        cases.append(case)

    db.add_all(cases)
    db.commit()

    print(
        f"SUCCESS: Generated {len(cases)} collection cases."
    )

    return cases
