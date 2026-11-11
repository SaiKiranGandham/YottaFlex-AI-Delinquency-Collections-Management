
import random

from datetime import date
from sqlalchemy.orm import Session

from config import RANDOM_SEED, AS_OF_DATE
from src.models.events import ContactPreference

CHANNELS = ["PHONE", "SMS", "EMAIL"]


def generate_contact_preferences(db: Session, customers):
    rng = random.Random(RANDOM_SEED + 6)

    reference_date = date.fromisoformat(AS_OF_DATE)
    preferences = []

    for customer in customers:
        restricted_customer = rng.random() < 0.10

        for channel in CHANNELS:
            preference = ContactPreference(
                preference_id=f"CP-{customer.customer_id}-{channel}",
                customer_id=customer.customer_id,
                channel=channel,
                allowed=not restricted_customer,
                preferred_start_time="09:00",
                preferred_end_time="18:00",
                effective_from=reference_date,
                effective_to=None,
            )

            preferences.append(preference)

    db.add_all(preferences)
    db.commit()

    print(
        f"SUCCESS: Generated {len(preferences)} contact preferences."
    )

    return preferences
