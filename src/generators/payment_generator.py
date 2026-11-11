
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from config import AS_OF_DATE
from src.models.entities import Loan, Installment
from src.models.events import CollectionCase, Payment


def generate_payments(
    db: Session,
    loans: list[Loan],
    installments: list[Installment],
    cases: list[CollectionCase],
):
    """Create payment events matching installment paid amounts."""

    reference_date = date.fromisoformat(AS_OF_DATE)

    case_by_loan = {
        case.loan_id: case
        for case in cases
    }

    payments = []
    payment_number = 1

    for installment in installments:

        amount_paid = installment.paid_amount

        # Do not create a payment for an unpaid installment.
        if amount_paid <= Decimal("0.00"):
            continue

        case = case_by_loan.get(installment.loan_id)

        payment = Payment(
            payment_id=f"PMT-2026-{payment_number:06d}",
            loan_id=installment.loan_id,
            installment_id=installment.installment_id,
            case_id=case.case_id if case else None,
            payment_amount=amount_paid,
            payment_date=min(installment.due_date, reference_date),
            payment_status="SUCCESS",
            payment_reference=f"REF-2026-{payment_number:06d}",
        )

        payments.append(payment)
        payment_number += 1

    db.add_all(payments)
    db.commit()

    print(f"SUCCESS: Generated {len(payments)} payment records.")

    return payments
