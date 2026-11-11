
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from config import AS_OF_DATE, GROUND_TRUTH_DIR
from src.database import SessionLocal
from src.models.entities import Loan, Installment, DelinquencySnapshot
from src.models.events import (
    CollectionCase,
    ContactAttempt,
    PromiseToPay,
    Payment,
)


def inject_edge_cases():
    db = SessionLocal()
    ground_truth = []

    try:
        reference_date = date.fromisoformat(AS_OF_DATE)

        loans = db.query(Loan).order_by(Loan.loan_id).all()
        cases = db.query(CollectionCase).all()
        attempts = db.query(ContactAttempt).all()
        payments = db.query(Payment).all()
        installments = db.query(Installment).all()
        snapshots = db.query(DelinquencySnapshot).all()

        case_number = len(cases) + 1

        # EDGE CASE 1:
        # Paid-off loan incorrectly remains in collections.
        paid_off_loan = next(
            (loan for loan in loans if loan.loan_status == "PAID_OFF"),
            None,
        )

        if paid_off_loan is None:
            raise ValueError("No paid-off loan available for edge case 1.")

        paid_case = CollectionCase(
            case_id=f"COL-2026-{case_number:06d}",
            loan_id=paid_off_loan.loan_id,
            case_status="OPEN",
            priority_score=Decimal("95.00"),
        )
        db.add(paid_case)
        db.flush()

        ground_truth.append({
            "edge_case": 1,
            "label": "PAID_ACCOUNT_IN_COLLECTION",
            "record_id": paid_case.case_id,
            "description": "A paid-off loan incorrectly has an open collection case.",
        })

        case_number += 1

        # EDGE CASE 2:
        # Contact attempt outside the permitted contact window.
        if not attempts:
            raise ValueError("No contact attempt available for edge case 2.")

        bad_attempt = sorted(
            attempts, key=lambda item: item.contact_attempt_id
        )[0]

        bad_attempt.attempted_at = datetime.combine(
            reference_date, time(23, 0)
        )

        ground_truth.append({
            "edge_case": 2,
            "label": "CONTACT_OUTSIDE_ALLOWED_WINDOW",
            "record_id": bad_attempt.contact_attempt_id,
            "description": "Contact was attempted at 23:00, outside the permitted window.",
        })

        # EDGE CASE 3:
        # Payment allocated to an installment belonging to another loan.
        if not payments:
            raise ValueError("No payment available for edge case 3.")

        bad_payment = sorted(
            payments, key=lambda item: item.payment_id
        )[0]

        wrong_installment = next(
            (
                item for item in installments
                if item.loan_id != bad_payment.loan_id
            ),
            None,
        )

        if wrong_installment is None:
            raise ValueError("No different-loan installment available.")

        bad_payment.installment_id = wrong_installment.installment_id

        ground_truth.append({
            "edge_case": 3,
            "label": "PAYMENT_WRONG_INSTALLMENT",
            "record_id": bad_payment.payment_id,
            "description": "Payment references an installment belonging to another loan.",
        })

        # EDGE CASE 4:
        # Promise amount exceeds the outstanding arrears.
        snapshot_by_loan = {
            item.loan_id: item for item in snapshots
        }

        case_with_arrears = next(
            (
                case for case in sorted(
                    cases, key=lambda item: item.case_id
                )
                if snapshot_by_loan.get(case.loan_id)
                and snapshot_by_loan[case.loan_id].arrears_amount
                > Decimal("0.00")
            ),
            None,
        )

        if case_with_arrears is None:
            raise ValueError("No collection case with arrears for edge case 4.")

        arrears = snapshot_by_loan[
            case_with_arrears.loan_id
        ].arrears_amount

        bad_promise = PromiseToPay(
            promise_id=f"PTP-{case_with_arrears.case_id}-EDGE001",
            case_id=case_with_arrears.case_id,
            promised_amount=arrears + Decimal("1000.00"),
            promised_date=reference_date + timedelta(days=7),
            promise_status="PENDING",
        )

        db.add(bad_promise)

        ground_truth.append({
            "edge_case": 4,
            "label": "PROMISE_EXCEEDS_ARREARS",
            "record_id": bad_promise.promise_id,
            "description": "Promised amount is 1000 more than outstanding arrears.",
        })

        # EDGE CASE 5:
        # Disputed debt incorrectly treated as confirmed for collections.
        disputed_snapshot = next(
            (
                snapshot for snapshot in snapshots
                if snapshot.dispute_flag
                and next(
                    loan for loan in loans
                    if loan.loan_id == snapshot.loan_id
                ).loan_status == "ACTIVE"
            ),
            None,
        )

        if disputed_snapshot is None:
            raise ValueError("No active disputed loan available for edge case 5.")

        disputed_loan = next(
            loan for loan in loans
            if loan.loan_id == disputed_snapshot.loan_id
        )

        disputed_case = next(
            (
                case for case in cases
                if case.loan_id == disputed_loan.loan_id
            ),
            None,
        )

        if disputed_case is None:
            disputed_case = CollectionCase(
                case_id=f"COL-2026-{case_number:06d}",
                loan_id=disputed_loan.loan_id,
                case_status="OPEN",
                priority_score=Decimal("90.00"),
            )
            db.add(disputed_case)
            db.flush()

        disputed_case.case_status = "OPEN"

        ground_truth.append({
            "edge_case": 5,
            "label": "DISPUTED_DEBT_TREATED_AS_CONFIRMED",
            "record_id": disputed_case.case_id,
            "description": "A disputed loan is incorrectly kept in an open collection case.",
        })

        db.commit()

        # Save expected edge-case labels separately.
        output_file = GROUND_TRUTH_DIR / "edge_cases.json"

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(ground_truth, file, indent=4)

        print("\n===================================")
        print(" EDGE CASE INJECTION COMPLETED")
        print("===================================")

        for item in ground_truth:
            print(
                f"Edge case {item['edge_case']}: "
                f"{item['label']}"
            )

        print(f"\nGround truth saved to: {output_file}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    inject_edge_cases()
