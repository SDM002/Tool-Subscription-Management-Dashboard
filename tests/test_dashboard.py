"""
tests/test_dashboard.py  [NEW]
Tests for dashboard summary, renewals, and insights endpoints.
Run with: pytest tests/test_dashboard.py -v
"""

import pytest
from datetime import date, timedelta


async def add_sub(client, **kwargs):
    defaults = {
        "tool_name": "Tool",
        "category": "Other",
        "price": 10.0,
        "billing_cycle": "monthly",
    }
    defaults.update(kwargs)
    return (await client.post("/api/subscriptions", json=defaults)).json()


@pytest.mark.asyncio
async def test_dashboard_empty(auth_client):
    client, _ = auth_client
    res = await client.get("/api/dashboard/summary")
    assert res.status_code == 200
    body = res.json()
    assert body["total_subscriptions"] == 0
    assert body["total_monthly_spend"] == 0.0


@pytest.mark.asyncio
async def test_dashboard_monthly_spend(auth_client):
    client, _ = auth_client
    await add_sub(client, tool_name="A", price=10.0, billing_cycle="monthly")
    await add_sub(client, tool_name="B", price=20.0, billing_cycle="monthly")
    # Yearly: 120 / 12 = 10/month
    await add_sub(client, tool_name="C", price=120.0, billing_cycle="yearly")

    res = await client.get("/api/dashboard/summary")
    body = res.json()
    assert body["total_monthly_spend"] == 40.0   # 10 + 20 + 10
    assert body["total_yearly_spend"] == 480.0   # 120 + 240 + 120


@pytest.mark.asyncio
async def test_dashboard_due_this_week(auth_client):
    client, _ = auth_client
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    next_month = (date.today() + timedelta(days=40)).isoformat()
    await add_sub(client, tool_name="DueSoon",  renewal_date=tomorrow)
    await add_sub(client, tool_name="NotDueSoon", renewal_date=next_month)

    res = await client.get("/api/dashboard/summary")
    body = res.json()
    assert len(body["due_this_week"]) == 1
    assert body["due_this_week"][0]["tool_name"] == "DueSoon"


@pytest.mark.asyncio
async def test_upcoming_renewals_endpoint(auth_client):
    client, _ = auth_client
    in_5_days  = (date.today() + timedelta(days=5)).isoformat()
    in_45_days = (date.today() + timedelta(days=45)).isoformat()
    await add_sub(client, tool_name="Soon",  renewal_date=in_5_days)
    await add_sub(client, tool_name="Later", renewal_date=in_45_days)

    res30 = await client.get("/api/dashboard/renewals?days=30")
    assert res30.status_code == 200
    assert len(res30.json()) == 1
    assert res30.json()[0]["tool_name"] == "Soon"

    res60 = await client.get("/api/dashboard/renewals?days=60")
    assert len(res60.json()) == 2


@pytest.mark.asyncio
async def test_insights_duplicates(auth_client):
    client, _ = auth_client
    await add_sub(client, tool_name="Figma",      category="Design")
    await add_sub(client, tool_name="Adobe XD",   category="Design")
    await add_sub(client, tool_name="Sketch",     category="Design")

    res = await client.get("/api/dashboard/insights")
    assert res.status_code == 200
    types = [i["type"] for i in res.json()]
    assert "duplicate" in types


@pytest.mark.asyncio
async def test_insights_annual_saving(auth_client):
    client, _ = auth_client
    # Monthly subscription with price > 5 should generate annual saving insight
    await add_sub(client, tool_name="Slack", price=15.0, billing_cycle="monthly")

    res = await client.get("/api/dashboard/insights")
    types = [i["type"] for i in res.json()]
    assert "annual_saving" in types
