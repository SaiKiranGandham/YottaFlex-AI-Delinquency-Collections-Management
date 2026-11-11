
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from config import RANDOM_SEED, AS_OF_DATE, INSTALLMENTS_PER_LOAN
from src.models.entities import Loan, Installment


def generate_installments(db: Session, loans: list[Loan]):
    """Generate installments across a 12-month schedule."""

    rng = random.Random(RANDOM_SEED + 4)
    reference_date = date.fromisoformat(AS_OF_DATE)

    installments = []

    for loan in loans:
        installment_amount = (
            loan.principal_amount / INSTALLMENTS_PER_LOAN
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        for number in range(1, INSTALLMENTS_PER_LOAN + 1):

            # Spread installments across 12 months.
            due_date = loan.start_date + timedelta(
                days=round(365 * number / INSTALLMENTS_PER_LOAN)
            )

            due_amount = installment_amount

            # Adjust the final installment for rounding differences.
            if number == INSTALLMENTS_PER_LOAN:
                due_amount = (
                    loan.principal_amount
                    - installment_amount * (INSTALLMENTS_PER_LOAN - 1)
                ).quantize(Decimal("0.01"))

            if loan.loan_status == "PAID_OFF":
                paid_amount = due_amount
                status = "PAID"

            elif due_date > reference_date:
                paid_amount = Decimal("0.00")
                status = "PENDING"

            else:
                outcome = rng.choices(
                    ["PAID", "PARTIAL", "OVERDUE"],
                    weights=[45, 20, 35],
                    k=1,
                )[0]

                if outcome == "PAID":
                    paid_amount = due_amount
                    status = "PAID"

                elif outcome == "PARTIAL":
                    paid_amount = (
                        due_amount * Decimal("0.50")
                    ).quantize(Decimal("0.01"))
                    status = "PARTIAL"

                else:
                    paid_amount = Decimal("0.00")
                    status = "OVERDUE"

            installment = Installment(
                installment_id=f"INS-{loan.loan_id}-{number:03d}",
                loan_id=loan.loan_id,
                installment_number=number,
                due_date=due_date,
                due_amount=due_amount,
                paid_amount=paid_amount,
                installment_status=status,
            )

            installments.append(installment)

    db.add_all(installments)
    db.commit()

    print(f"SUCCESS: Generated {len(installments)} installments.")

    return installments
