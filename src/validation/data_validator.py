
from datetime import date
from decimal import Decimal
from collections import defaultdict

from sqlalchemy import text

from config import AS_OF_DATE
from src.database import SessionLocal
from src.models.entities import (
    Customer,
    Account,
    Loan,
    Installment,
    DelinquencySnapshot,
)
from src.models.events import (
    ContactPreference,
    CollectionCase,
    ContactAttempt,
    PromiseToPay,
    Payment,
)


def validate_data():
    db = SessionLocal()
    errors = []

    try:
        reference_date = date.fromisoformat(AS_OF_DATE)

        customers = db.query(Customer).all()
        accounts = db.query(Account).all()
        loans = db.query(Loan).all()
        installments = db.query(Installment).all()
        snapshots = db.query(DelinquencySnapshot).all()
        preferences = db.query(ContactPreference).all()
        cases = db.query(CollectionCase).all()
        attempts = db.query(ContactAttempt).all()
        promises = db.query(PromiseToPay).all()
        payments = db.query(Payment).all()

        print("\n===================================")
        print(" YOTTAFLEX DATA VALIDATION")
        print("===================================")

        # 1. Record counts
        print("\n1. RECORD COUNTS")
        tables = {
            "Customers": customers,
            "Accounts": accounts,
            "Loans": loans,
            "Installments": installments,
            "Snapshots": snapshots,
            "Contact preferences": preferences,
            "Collection cases": cases,
            "Contact attempts": attempts,
            "Promises": promises,
            "Payments": payments,
        }

        for name, records in tables.items():
            print(f"{name}: {len(records)}")

        if len(accounts) != len(customers):
            errors.append("Customer and account counts do not match.")

        if len(loans) != len(accounts):
            errors.append("Account and loan counts do not match.")

        if len(installments) != len(loans) * 3:
            errors.append("Expected exactly 3 installments per loan.")

        if len(snapshots) != len(loans):
            errors.append("Expected one snapshot per loan.")

        if len(preferences) != len(customers) * 3:
            errors.append("Expected 3 contact preferences per customer.")

        # 2. Foreign key integrity
        print("\n2. FOREIGN KEY CHECK")

        fk_errors = db.execute(
            text("PRAGMA foreign_key_check")
        ).fetchall()

        if fk_errors:
            errors.append(
                f"Foreign key violations found: {len(fk_errors)}"
            )
        else:
            print("PASS: No foreign key violations.")

        # 3. Installment arithmetic
        print("\n3. INSTALLMENT CHECK")

        installments_by_loan = defaultdict(list)
        loan_by_id = {loan.loan_id: loan for loan in loans}

        for item in installments:
            installments_by_loan[item.loan_id].append(item)

            if item.paid_amount > item.due_amount:
                errors.append(
                    f"Payment exceeds due amount: {item.installment_id}"
                )

            if item.paid_amount < Decimal("0.00"):
                errors.append(
                    f"Negative paid amount: {item.installment_id}"
                )

            loan = loan_by_id.get(item.loan_id)

            # Paid-off loans may have future installments paid early.
            if loan and loan.loan_status == "PAID_OFF":
                if item.paid_amount != item.due_amount:
                    errors.append(
                        f"Paid-off loan has unpaid installment: "
                        f"{item.installment_id}"
                    )
                elif item.installment_status != "PAID":
                    errors.append(
                        f"Paid-off loan installment is not marked PAID: "
                        f"{item.installment_id}"
                    )

            elif item.due_date > reference_date:
                if item.installment_status != "PENDING":
                    errors.append(
                        f"Future installment is not pending: "
                        f"{item.installment_id}"
                    )

            elif item.paid_amount == item.due_amount:
                if item.installment_status != "PAID":
                    errors.append(
                        f"Fully paid installment has wrong status: "
                        f"{item.installment_id}"
                    )

            elif item.paid_amount > Decimal("0.00"):
                if item.installment_status != "PARTIAL":
                    errors.append(
                        f"Partially paid installment has wrong status: "
                        f"{item.installment_id}"
                    )

            elif item.installment_status != "OVERDUE":
                errors.append(
                    f"Unpaid past-due installment has wrong status: "
                    f"{item.installment_id}"
                )

        for loan_id, loan_items in installments_by_loan.items():
            loan = loan_by_id[loan_id]

            total_due = sum(
                (item.due_amount for item in loan_items),
                Decimal("0.00"),
            )

            if total_due != loan.principal_amount:
                errors.append(
                    f"Installment total does not match principal: {loan_id}"
                )

            if loan.loan_status == "PAID_OFF":
                if any(
                    item.paid_amount != item.due_amount
                    for item in loan_items
                ):
                    errors.append(
                        f"Paid-off loan has unpaid installments: {loan_id}"
                    )

        # 4. Delinquency calculation
        print("\n4. DELINQUENCY CHECK")

        snapshot_by_loan = {
            item.loan_id: item for item in snapshots
        }

        for loan in loans:
            loan_items = installments_by_loan.get(loan.loan_id, [])

            overdue = [
                item for item in loan_items
                if item.due_date < reference_date
                and item.due_amount > item.paid_amount
            ]

            expected_arrears = sum(
                (
                    item.due_amount - item.paid_amount
                    for item in overdue
                ),
                Decimal("0.00"),
            )

            expected_dpd = 0

            if overdue:
                oldest_due_date = min(
                    item.due_date for item in overdue
                )
                expected_dpd = (
                    reference_date - oldest_due_date
                ).days

            snapshot = snapshot_by_loan.get(loan.loan_id)

            if snapshot is None:
                errors.append(
                    f"Missing delinquency snapshot: {loan.loan_id}"
                )
                continue

            if snapshot.arrears_amount != expected_arrears:
                errors.append(
                    f"Incorrect arrears amount: {loan.loan_id}"
                )

            if snapshot.days_past_due != expected_dpd:
                errors.append(
                    f"Incorrect DPD: {loan.loan_id}"
                )

        # 5. Payment reconciliation
        print("\n5. PAYMENT RECONCILIATION")

        payment_totals = defaultdict(
            lambda: Decimal("0.00")
        )

        for payment in payments:
            if payment.installment_id:
                payment_totals[payment.installment_id] += (
                    payment.payment_amount
                )

        for item in installments:
            actual_paid = payment_totals[item.installment_id]

            if actual_paid != item.paid_amount:
                errors.append(
                    f"Payment mismatch: {item.installment_id}"
                )

        # 6. Contact compliance
        print("\n6. CONTACT COMPLIANCE")

        preference_map = {
            (item.customer_id, item.channel): item
            for item in preferences
        }

        account_by_id = {
            item.account_id: item for item in accounts
        }

        case_by_id = {
            item.case_id: item for item in cases
        }

        loan_by_id = {
            item.loan_id: item for item in loans
        }

        for attempt in attempts:
            case = case_by_id.get(attempt.case_id)

            if case is None:
                errors.append(
                    f"Contact attempt has no case: "
                    f"{attempt.contact_attempt_id}"
                )
                continue

            loan = loan_by_id.get(case.loan_id)
            account = account_by_id.get(loan.account_id) if loan else None

            if account is None:
                errors.append(
                    f"Contact attempt has no customer account: "
                    f"{attempt.contact_attempt_id}"
                )
                continue

            preference = preference_map.get(
                (account.customer_id, attempt.channel)
            )

            if preference is None or not preference.allowed:
                errors.append(
                    f"Contact attempt used a restricted channel: "
                    f"{attempt.contact_attempt_id}"
                )
                continue

            attempted_time = attempt.attempted_at.time()

            if not (
                preference.preferred_start_time
                <= attempted_time.strftime("%H:%M")
                <= preference.preferred_end_time
            ):
                errors.append(
                    f"Contact outside allowed time: "
                    f"{attempt.contact_attempt_id}"
                )

        # 7. Promise amount check
        print("\n7. PROMISE CHECK")

        case_by_id = {item.case_id: item for item in cases}
        snapshot_by_loan = {item.loan_id: item for item in snapshots}

        for promise in promises:
            case = case_by_id.get(promise.case_id)

            if case is None:
                errors.append(
                    f"Promise has no collection case: {promise.promise_id}"
                )
                continue

            snapshot = snapshot_by_loan.get(case.loan_id)

            if (
                snapshot
                and promise.promised_amount > snapshot.arrears_amount
            ):
                errors.append(
                    f"Promise exceeds arrears: {promise.promise_id}"
                )

        # 8. Final result
        print("\n===================================")

        if errors:
            print(f"VALIDATION FAILED: {len(errors)} issue(s)")
            for number, error in enumerate(errors, start=1):
                print(f"{number}. {error}")
        else:
            print("VALIDATION PASSED!")
            print("No validation errors found.")

        print("===================================")

        return len(errors) == 0

    finally:
        db.close()


if __name__ == "__main__":
    success = validate_data()

    if not success:
        raise SystemExit(1)
