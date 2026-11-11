
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from config import AS_OF_DATE

DEFAULT_RECORD_TIMESTAMP = datetime.combine(
    date.fromisoformat(AS_OF_DATE),
    time.min,
)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=DEFAULT_RECORD_TIMESTAMP
    )

    accounts: Mapped[list["Account"]] = relationship(back_populates="customer")


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"), nullable=False
    )
    account_status: Mapped[str] = mapped_column(String(20), nullable=False)
    opened_date: Mapped[date] = mapped_column(Date, nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="accounts")
    loans: Mapped[list["Loan"]] = relationship(back_populates="account")


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("principal_amount > 0", name="ck_loan_principal_positive"),
        CheckConstraint("interest_rate >= 0", name="ck_loan_interest_nonnegative"),
    )

    loan_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.account_id"), nullable=False
    )
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    loan_status: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)

    account: Mapped["Account"] = relationship(back_populates="loans")
    installments: Mapped[list["Installment"]] = relationship(back_populates="loan")


class Installment(Base):
    __tablename__ = "installments"
    __table_args__ = (
        CheckConstraint("due_amount > 0", name="ck_installment_due_positive"),
        CheckConstraint("paid_amount >= 0", name="ck_installment_paid_nonnegative"),
    )

    installment_id: Mapped[str] = mapped_column(String(60), primary_key=True)
    loan_id: Mapped[str] = mapped_column(
        ForeignKey("loans.loan_id"), nullable=False
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    installment_status: Mapped[str] = mapped_column(String(20), nullable=False)

    loan: Mapped["Loan"] = relationship(back_populates="installments")


class DelinquencySnapshot(Base):
    __tablename__ = "delinquency_snapshots"
    __table_args__ = (
        CheckConstraint("days_past_due >= 0", name="ck_snapshot_dpd_nonnegative"),
        CheckConstraint("arrears_amount >= 0", name="ck_snapshot_arrears_nonnegative"),
    )

    snapshot_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    loan_id: Mapped[str] = mapped_column(
        ForeignKey("loans.loan_id"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_past_due: Mapped[int] = mapped_column(Integer, nullable=False)
    arrears_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    risk_category: Mapped[str] = mapped_column(String(20), nullable=False)
    hardship_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dispute_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
