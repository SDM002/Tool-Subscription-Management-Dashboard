"""
seed.py  [NEW]

Populate the database with a demo user and realistic sample subscriptions.
Run once after first startup to have data ready for testing.

Usage:
    python seed.py

Creates:
    Email:    demo@example.com
    Password: Demo1234

WARNING: Only run in development. Do not seed production databases.
"""

import asyncio
from datetime import date, timedelta

from app.core.database import create_tables, get_db_context
from app.core.security import hash_password
from app.models.subscription import BillingCycle, Subscription
from app.models.user import User

# ── Demo credentials ─────────────────────────────────────────
DEMO_EMAIL    = "demo@example.com"
DEMO_PASSWORD = "Demo1234"
DEMO_NAME     = "Demo User"

# ── Sample subscriptions ──────────────────────────────────────
today = date.today()

SAMPLE_SUBS = [
    # Productivity
    dict(tool_name="Notion",        category="Productivity",    price=16.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=5),  currency="USD", start_date=today - timedelta(days=25),  notes="Team workspace"),
    dict(tool_name="Todoist",       category="Productivity",    price=4.00,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=18), currency="USD", start_date=today - timedelta(days=12)),
    # Design
    dict(tool_name="Figma",         category="Design",          price=15.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=3),  currency="USD", start_date=today - timedelta(days=57),  notes="Pro plan"),
    dict(tool_name="Adobe CC",      category="Design",          price=54.99, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=22), currency="USD", start_date=today - timedelta(days=8)),
    # Development
    dict(tool_name="GitHub Pro",    category="Development",     price=4.00,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=11), currency="USD", start_date=today - timedelta(days=19)),
    dict(tool_name="Vercel Pro",    category="Development",     price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=45), currency="USD", start_date=today - timedelta(days=15)),
    dict(tool_name="JetBrains All", category="Development",     price=77.90, billing_cycle=BillingCycle.YEARLY,    renewal_date=today + timedelta(days=180),currency="USD", start_date=today - timedelta(days=185), notes="All Products Pack"),
    # Communication
    dict(tool_name="Slack Pro",     category="Communication",   price=8.75,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=2),  currency="USD", start_date=today - timedelta(days=28)),
    dict(tool_name="Loom Business", category="Communication",   price=12.50, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=33), currency="USD"),
    # Storage & Cloud
    dict(tool_name="Dropbox Plus",  category="Storage & Cloud", price=11.99, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=14), currency="USD"),
    dict(tool_name="AWS",           category="Storage & Cloud", price=45.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=7),  currency="USD", notes="Variable — estimated avg"),
    # Security
    dict(tool_name="1Password",     category="Security",        price=2.99,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=9),  currency="USD"),
    # AI & ML
    dict(tool_name="ChatGPT Plus",  category="AI & ML",         price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=6),  currency="USD"),
    dict(tool_name="Claude Pro",    category="AI & ML",         price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=27), currency="USD"),
    # Analytics
    dict(tool_name="Mixpanel",      category="Analytics",       price=28.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today + timedelta(days=50), currency="USD", notes="Growth plan"),
]


async def seed() -> None:
    import app.models  # noqa: F401 — register all models

    await create_tables()
    print("✅ Tables ready.")

    async with get_db_context() as db:
        from sqlalchemy import select

        # Check if demo user already exists
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"ℹ️  Demo user already exists (id={existing.id}). Skipping.")
            return

        # Create user
        user = User(
            email=DEMO_EMAIL,
            full_name=DEMO_NAME,
            hashed_password=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        await db.flush()
        print(f"✅ Created user: {DEMO_EMAIL} (id={user.id})")

        # Create subscriptions
        for s in SAMPLE_SUBS:
            sub = Subscription(user_id=user.id, **s)
            db.add(sub)

        await db.flush()
        print(f"✅ Seeded {len(SAMPLE_SUBS)} subscriptions.")

    print("\n🚀 Seed complete!")
    print(f"   Login → Email:    {DEMO_EMAIL}")
    print(f"           Password: {DEMO_PASSWORD}")
    print("\n   Open http://localhost:8000 and sign in.")


if __name__ == "__main__":
    asyncio.run(seed())
