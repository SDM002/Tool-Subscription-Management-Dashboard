import asyncio
from datetime import date, timedelta

async def seed():
    import app.models  # noqa: F401
    from app.core.database import create_tables, get_db_context
    from app.core.security import hash_password
    from app.models.user import User
    from app.models.subscription import BillingCycle, Subscription
    from sqlalchemy import select

    await create_tables()
    print("✅ Tables ready.")

    today = date.today()

    SUBS = [
        dict(tool_name="Notion",         category="Productivity",    price=16.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=5),   currency="USD"),
        dict(tool_name="Figma",          category="Design",          price=15.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=3),   currency="USD", notes="Pro plan"),
        dict(tool_name="Adobe CC",       category="Design",          price=54.99, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=22),  currency="USD"),
        dict(tool_name="GitHub Pro",     category="Development",     price=4.00,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=11),  currency="USD"),
        dict(tool_name="Vercel Pro",     category="Development",     price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=45),  currency="USD"),
        dict(tool_name="JetBrains All",  category="Development",     price=77.90, billing_cycle=BillingCycle.YEARLY,    renewal_date=today+timedelta(days=180), currency="USD"),
        dict(tool_name="Slack Pro",      category="Communication",   price=8.75,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=2),   currency="USD"),
        dict(tool_name="Loom Business",  category="Communication",   price=12.50, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=33),  currency="USD"),
        dict(tool_name="Dropbox Plus",   category="Storage & Cloud", price=11.99, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=14),  currency="USD"),
        dict(tool_name="AWS",            category="Storage & Cloud", price=45.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=7),   currency="USD", notes="Estimated avg"),
        dict(tool_name="1Password",      category="Security",        price=2.99,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=9),   currency="USD"),
        dict(tool_name="ChatGPT Plus",   category="AI & ML",         price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=6),   currency="USD"),
        dict(tool_name="Claude Pro",     category="AI & ML",         price=20.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=27),  currency="USD"),
        dict(tool_name="Mixpanel",       category="Analytics",       price=28.00, billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=50),  currency="USD"),
        dict(tool_name="Todoist",        category="Productivity",    price=4.00,  billing_cycle=BillingCycle.MONTHLY,   renewal_date=today+timedelta(days=18),  currency="USD"),
    ]

    async with get_db_context() as db:
        result = await db.execute(select(User).where(User.email == "demo@example.com"))
        if result.scalar_one_or_none():
            print("ℹ️  Demo user already exists — skipping.")
            return

        user = User(
            email="demo@example.com",
            full_name="Demo User",
            hashed_password=hash_password("Demo1234"),
        )
        db.add(user)
        await db.flush()
        print(f"✅ Created user: demo@example.com (id={user.id})")

        for s in SUBS:
            db.add(Subscription(user_id=user.id, **s))
        await db.flush()
        print(f"✅ Seeded {len(SUBS)} subscriptions.")

    print("\n🚀 Done!")
    print("   Email:    demo@example.com")
    print("   Password: Demo1234")
    print("   Open:     http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(seed())
