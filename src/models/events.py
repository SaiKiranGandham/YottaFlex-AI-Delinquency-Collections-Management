
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config import AS_OF_DATE
from src.models.entities import Base

DEFAULT_RECORD_TIMESTAMP = datetime.combine(
    date.fromisoformat(AS_OF_DATE),
    time.min,
)


class ContactPreference(Base):
    __tablename__ = "contact_preferences"

    preference_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preferred_start_time: Mapped[str | None] = mapped_column(String(10))
    preferred_end_time: Mapped[str | None] = mapped_column(String(10))
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=DEFAULT_RECORD_TIMESTAMP
    )


class CollectionCase(Base):
    __tablename__ = "collection_cases"

    case_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    loan_id: Mapped[str] = mapped_column(
        ForeignKey("loans.loan_id"), nullable=False
    )
    case_status: Mapped[str] = mapped_column(String(20), nullable=False)
    priority_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )
    assigned_to: Mapped[str | None] = mapped_column(String(100))
    opened_at: Mapped[datetime] = mapped_column(
        DateTime, default=DEFAULT_RECORD_TIMESTAMP
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    closure_reason: Mapped[str | None] = mapped_column(String(100))

    contact_attempts: Mapped[list["ContactAttempt"]] = relationship(
        back_populates="collection_case"
    )
    promises: Mapped[list["PromiseToPay"]] = relationship(
        back_populates="collection_case"
    )


class ContactAttempt(Base):
    __tablename__ = "contact_attempts"

    contact_attempt_id: Mapped[str] = mapped_column(
        String(60), primary_key=True
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("collection_cases.case_id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)

    collection_case: Mapped["CollectionCase"] = relationship(
        back_populates="contact_attempts"
    )


class PromiseToPay(Base):
    __tablename__ = "promises_to_pay"
    __table_args__ = (
        CheckConstraint(
            "promised_amount > 0",
            name="ck_promise_amount_positive",
        ),
    )

    promise_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        ForeignKey("collection_cases.case_id"), nullable=False
    )
    promised_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    promised_date: Mapped[date] = mapped_column(Date, nullable=False)
    promise_status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=DEFAULT_RECORD_TIMESTAMP
    )
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime)

    collection_case: Mapped["CollectionCase"] = relationship(
        back_populates="promises"
    )


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "payment_amount > 0",
            name="ck_payment_amount_positive",
        ),
    )

    payment_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    loan_id: Mapped[str] = mapped_column(
        ForeignKey("loans.loan_id"), nullable=False
    )
    installment_id: Mapped[str | None] = mapped_column(
        ForeignKey("installments.installment_id")
    )
    case_id: Mapped[str | None] = mapped_column(
        ForeignKey("collection_cases.case_id")
    )
    payment_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(
        String(80), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=DEFAULT_RECORD_TIMESTAMP
    )
