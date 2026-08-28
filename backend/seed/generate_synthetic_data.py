"""
FinSight Synthetic Data Generator
Populates the SQLite database with realistic deterministic financial data.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from backend.db import Base, SessionLocal, engine
from backend.models.account import Account
from backend.models.bill import Bill
from backend.models.document import Document
from backend.models.goal import Goal
from backend.models.transaction import Transaction
from backend.models.user import User


def seed_database():
    """Drops and recreates all tables, seeding deterministic data for demo_user."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        start_of_this_month = datetime(now.year, now.month, 1, 10, 0, 0, tzinfo=timezone.utc)

        # Calculate previous month date
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_month = now.month - 1 if now.month > 1 else 12
        start_of_last_month = datetime(prev_year, prev_month, 1, 10, 0, 0, tzinfo=timezone.utc)

        # 1. Create User
        user = User(
            id="demo_user",
            name="Aditi Sharma",
            email="aditi.sharma@example.com",
            created_at=start_of_last_month - timedelta(days=30),
        )
        db.add(user)
        db.flush()

        # 2. Create Account
        account = Account(
            id="acc_primary_001",
            user_id="demo_user",
            name="HDFC Salary Account",
            account_type="savings",
            balance=Decimal("138372.00"),
            currency="INR",
        )
        db.add(account)
        db.flush()

        # 3. Seed Transactions
        # Net sum must equal 138,372.00 exactly.
        # Income:
        # Salary last month: +100000.00
        # Salary this month: +100000.00
        # Freelance Income: +25000.00
        # Total Income = 225,000.00
        #
        # Expenses:
        # Target Net Balance = 138,372.00
        # Total Expenses needed = 225,000.00 - 138,372.00 = 86,628.00
        #
        # Last Month Food = 10,168.95 (so this month 12,400.00 gives exactly 21.94% increase)
        # (12400.00 - 10168.95) / 10168.95 * 100 = 21.9403% -> quantize 21.94%

        txs = [
            # Income Last Month
            Transaction(
                id="tx_inc_001",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("100000.00"),
                category="Income",
                description="Salary Credit",
                timestamp=start_of_last_month + timedelta(days=1),
                is_recurring=True,
            ),
            # Income This Month
            Transaction(
                id="tx_inc_002",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("100000.00"),
                category="Income",
                description="Salary Credit",
                timestamp=start_of_this_month + timedelta(days=1),
                is_recurring=True,
            ),
            Transaction(
                id="tx_inc_003",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("25000.00"),
                category="Income",
                description="Freelance Design Project",
                timestamp=start_of_this_month + timedelta(days=5),
                is_recurring=False,
            ),
            # Last Month Expenses
            Transaction(
                id="tx_exp_lm_rent",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-25000.00"),
                category="Bills",
                description="Rent Payment",
                timestamp=start_of_last_month + timedelta(days=2),
                is_recurring=True,
            ),
            Transaction(
                id="tx_exp_lm_food",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-10168.95"),
                category="Food",
                description="Dining & Groceries",
                timestamp=start_of_last_month + timedelta(days=10),
                is_recurring=False,
            ),
            Transaction(
                id="tx_exp_lm_trans",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-3500.00"),
                category="Transport",
                description="Metro & Fuel",
                timestamp=start_of_last_month + timedelta(days=15),
                is_recurring=False,
            ),
            Transaction(
                id="tx_exp_lm_shop",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-4000.00"),
                category="Shopping",
                description="Apparel",
                timestamp=start_of_last_month + timedelta(days=18),
                is_recurring=False,
            ),
            # This Month Expenses (Total this month = 43,959.05)
            Transaction(
                id="tx_exp_tm_rent",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-14000.00"),
                category="Bills",
                description="Electricity & Utilities",
                timestamp=start_of_this_month + timedelta(days=2),
                is_recurring=True,
            ),
            Transaction(
                id="tx_exp_tm_food1",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-620.00"),
                category="Food",
                description="Dinner with friends",
                timestamp=start_of_this_month + timedelta(days=3),
                is_recurring=False,
            ),
            Transaction(
                id="tx_exp_tm_food2",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-11780.00"),
                category="Food",
                description="Supermarket Groceries & Meals",
                timestamp=start_of_this_month + timedelta(days=6),
                is_recurring=False,
            ),
            Transaction(
                id="tx_exp_tm_trans",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-3500.00"),
                category="Transport",
                description="Cab & Transit",
                timestamp=start_of_this_month + timedelta(days=7),
                is_recurring=False,
            ),
            Transaction(
                id="tx_exp_tm_shop",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-8200.00"),
                category="Shopping",
                description="Electronics & Accessories",
                timestamp=start_of_this_month + timedelta(days=8),
                is_recurring=False,
            ),
            Transaction(
                id="tx_exp_tm_ent",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-4100.00"),
                category="Entertainment",
                description="Movies & Concert",
                timestamp=start_of_this_month + timedelta(days=9),
                is_recurring=False,
            ),
            Transaction(
                id="tx_exp_tm_health",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-1200.00"),
                category="Healthcare",
                description="Pharmacy",
                timestamp=start_of_this_month + timedelta(days=10),
                is_recurring=False,
            ),
            # Balancing transaction to get exactly ₹138,372.00 net balance
            # Total so far: 225000 - (25000 + 10168.95 + 3500 + 4000 + 14000 + 620 + 11780 + 3500 + 8200 + 4100 + 1200)
            # = 225000 - 86068.95 = 138931.05
            # Target = 138372.00 -> Difference = 138931.05 - 138372.00 = 559.05 in 'Other'
            Transaction(
                id="tx_exp_tm_other",
                user_id="demo_user",
                account_id="acc_primary_001",
                amount=Decimal("-559.05"),
                category="Other",
                description="Miscellaneous Subscriptions",
                timestamp=start_of_this_month + timedelta(days=11),
                is_recurring=False,
            ),
        ]
        db.add_all(txs)

        # 4. Seed Goals
        # Emergency Fund: Target 200,000, Current 80,000, Monthly contribution 20,000 -> 6.0 months remaining
        goal_efund = Goal(
            id="goal_efund_001",
            user_id="demo_user",
            name="Emergency Fund",
            target_amount=Decimal("200000.00"),
            current_amount=Decimal("80000.00"),
            monthly_contribution=Decimal("20000.00"),
            target_date=now + timedelta(days=180),
            created_at=start_of_last_month,
        )
        db.add(goal_efund)

        goal_vacation = Goal(
            id="goal_vacation_002",
            user_id="demo_user",
            name="Vacation to Japan",
            target_amount=Decimal("150000.00"),
            current_amount=Decimal("30000.00"),
            monthly_contribution=Decimal("15000.00"),
            target_date=now + timedelta(days=240),
            created_at=start_of_last_month,
        )
        db.add(goal_vacation)

        # 5. Seed Bills
        bill1 = Bill(
            id="bill_001",
            user_id="demo_user",
            name="Apartment Maintenance & Electricity",
            amount=Decimal("5000.00"),
            due_date=now + timedelta(days=10),
            category="Bills",
            is_paid=False,
            is_recurring=True,
        )
        db.add(bill1)

        bill2 = Bill(
            id="bill_002",
            user_id="demo_user",
            name="Broadband & Mobile",
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=15),
            category="Bills",
            is_paid=False,
            is_recurring=True,
        )
        db.add(bill2)

        # 6. Seed Document
        doc = Document(
            id="doc_001",
            user_id="demo_user",
            title="Aug Grocery Bill",
            content="Items: Vegetables, Fruits, Milk. Total: 620",
            doc_type="receipt",
        )
        db.add(doc)

        db.commit()
        print("Database successfully seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
