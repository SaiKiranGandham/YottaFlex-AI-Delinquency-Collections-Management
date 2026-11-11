
import random
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from config import RANDOM_SEED, AS_OF_DATE
from src.models.entities import Loan, Account
from src.models.events import (
    CollectionCase,
    ContactAttempt,
    ContactPreference,
)


def generate_contact_attempts(
    db: Session,
    cases: list[CollectionCase],
    loans: list[Loan],
    accounts: list[Account],
    preferences: list[ContactPreference],
):
    """Generate contact attempts only through permitted channels."""

    rng = random.Random(RANDOM_SEED + 10)
    reference_date = date.fromisoformat(AS_OF_DATE)

    loan_by_id = {loan.loan_id: loan for loan in loans}
    account_by_id = {
        account.account_id: account for account in accounts
    }

    allowed_channels = {}

    for preference in preferences:
        if preference.allowed:
            allowed_channels.setdefault(
                preference.customer_id, []
            ).append(preference.channel)

    attempts = []

    for number, case in enumerate(cases, start=1):
        loan = loan_by_id.get(case.loan_id)

        if loan is None:
            continue

        account = account_by_id.get(loan.account_id)

        if account is None:
            continue

        channels = allowed_channels.get(account.customer_id, [])

        if not channels:
            continue

        channel = rng.choice(channels)

        # Schedule within the permitted 09:00–18:00 window.
        contact_time = time(
            hour=rng.randint(9, 17),
            minute=rng.choice([0, 15, 30, 45]),
        )

        attempted_at = datetime.combine(
            reference_date, contact_time
        )

        attempt = ContactAttempt(
            contact_attempt_id=f"CTP-{case.case_id}-{number:03d}",
            case_id=case.case_id,
            channel=channel,
            attempted_at=attempted_at,
            outcome=rng.choice(
                ["CONNECTED", "NO_ANSWER", "CALLBACK_REQUESTED"]
            ),
            agent_id=f"AGENT-{rng.randint(1, 20):03d}",
            notes="Synthetic contact attempt for testing.",
        )

        attempts.append(attempt)

    db.add_all(attempts)
    db.commit()

    print(
        f"SUCCESS: Generated {len(attempts)} permitted contact attempts."
    )

    return attempts
