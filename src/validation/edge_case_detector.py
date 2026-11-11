
import json
from datetime import date
from decimal import Decimal

from config import AS_OF_DATE, PROCESSED_DATA_DIR
from src.database import SessionLocal
from src.models.entities import (
    Loan,
    Account,
    Installment,
    DelinquencySnapshot,
)
from src.models.events import (
    CollectionCase,
    ContactAttempt,
    ContactPreference,
    PromiseToPay,
    Payment,
)


def detect_edge_cases():
    db = SessionLocal()
    detected = []

    try:
        reference_date = date.fromisoformat(AS_OF_DATE)

        loans = db.query(Loan).all()
        accounts = db.query(Account).all()
        installments = db.query(Installment).all()
        snapshots = db.query(DelinquencySnapshot).all()
        cases = db.query(CollectionCase).all()
        attempts = db.query(ContactAttempt).all()
        preferences = db.query(ContactPreference).all()
        promises = db.query(PromiseToPay).all()
        payments = db.query(Payment).all()

        loan_by_id = {item.loan_id: item for item in loans}
        account_by_id = {item.account_id: item for item in accounts}
        installment_by_id = {
            item.installment_id: item for item in installments
        }
        snapshot_by_loan = {
            item.loan_id: item for item in snapshots
        }
        case_by_id = {item.case_id: item for item in cases}

        def report(label, record_id, description):
            detected.append({
                "label": label,
                "record_id": record_id,
                "description": description,
            })

        # 1. Detect paid-off loans still in open collection cases.
        for case in cases:
            loan = loan_by_id.get(case.loan_id)

            if (
                loan
                and loan.loan_status == "PAID_OFF"
                and case.case_status == "OPEN"
            ):
                report(
                    "PAID_ACCOUNT_IN_COLLECTION",
                    case.case_id,
                    "Paid-off loan has an open collection case.",
                )

        # 2. Detect contact attempts outside permitted windows.
        preference_map = {
            (item.customer_id, item.channel): item
            for item in preferences
        }

        for attempt in attempts:
            case = case_by_id.get(attempt.case_id)

            if not case:
                continue

            loan = loan_by_id.get(case.loan_id)

            if not loan:
                continue

            account = account_by_id.get(loan.account_id)

            if not account:
                continue

            preference = preference_map.get(
                (account.customer_id, attempt.channel)
            )

            if not preference or not preference.allowed:
                report(
                    "CONTACT_OUTSIDE_ALLOWED_WINDOW",
                    attempt.contact_attempt_id,
                    "Contact used a missing or restricted channel.",
                )
                continue

            attempted_time = attempt.attempted_at.strftime("%H:%M")

            if not (
                preference.preferred_start_time
                <= attempted_time
                <= preference.preferred_end_time
            ):
                report(
                    "CONTACT_OUTSIDE_ALLOWED_WINDOW",
                    attempt.contact_attempt_id,
                    "Contact occurred outside the permitted time window.",
                )

        # 3. Detect payments allocated to another loan's installment.
        for payment in payments:
            if not payment.installment_id:
                continue

            installment = installment_by_id.get(
                payment.installment_id
            )

            if (
                installment
                and installment.loan_id != payment.loan_id
            ):
                report(
                    "PAYMENT_WRONG_INSTALLMENT",
                    payment.payment_id,
                    "Payment loan does not match installment loan.",
                )

        # 4. Detect promises exceeding outstanding arrears.
        for promise in promises:
            case = case_by_id.get(promise.case_id)

            if not case:
                continue

            snapshot = snapshot_by_loan.get(case.loan_id)

            if (
                snapshot
                and promise.promised_amount > snapshot.arrears_amount
            ):
                report(
                    "PROMISE_EXCEEDS_ARREARS",
                    promise.promise_id,
                    "Promised amount exceeds outstanding arrears.",
                )

        # 5. Detect disputed debt still in open collections.
        for case in cases:
            snapshot = snapshot_by_loan.get(case.loan_id)

            if (
                snapshot
                and snapshot.dispute_flag
                and case.case_status == "OPEN"
            ):
                report(
                    "DISPUTED_DEBT_TREATED_AS_CONFIRMED",
                    case.case_id,
                    "Disputed debt incorrectly remains in an open collection case.",
                )

        # Save detection results separately from ground truth.
        output_file = (
            PROCESSED_DATA_DIR / "detected_edge_cases.json"
        )

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(detected, file, indent=4)

        print("\n===================================")
        print(" EDGE CASE DETECTION RESULTS")
        print("===================================")

        for item in detected:
            print(
                f"DETECTED: {item['label']} "
                f"| Record: {item['record_id']}"
            )

        print("-----------------------------------")
        print(f"Total detected issues: {len(detected)}")
        print(f"Results saved to: {output_file}")
        print("===================================")

        return detected

    finally:
        db.close()


if __name__ == "__main__":
    detect_edge_cases()
