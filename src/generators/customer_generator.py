
import random

from faker import Faker
from sqlalchemy.orm import Session

from config import RANDOM_SEED
from src.models.entities import Customer


def generate_customers(db: Session, count: int = 100):
    fake = Faker("en_IN")
    fake.seed_instance(RANDOM_SEED)

    rng = random.Random(RANDOM_SEED + 1)

    customers = []

    for number in range(1, count + 1):
        customer = Customer(
            customer_id=f"CUST-{number:06d}",
            full_name=fake.name(),
            email=f"customer{number}@example.com",
            phone=f"9{rng.randint(100000000, 999999999)}",
        )
        customers.append(customer)

    db.add_all(customers)
    db.commit()

    print(f"SUCCESS: Generated {len(customers)} customers.")
    return customers
