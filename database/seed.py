"""
Seed illustrative catalog data for Idea Bank, Franchises, Auctions, and
Investment Opportunities, so those pages show real rows instead of an empty
list on a freshly migrated database.

Every row is explicitly verification_status="demo" -- these are illustrative
examples, not real listings, and the frontend labels them as such (see
apps/web/app/opportunities/page.tsx and the FeaturePage "in progress" badge).
No fabricated funding amounts are presented as fact; figures are round,
plausible placeholders for layout/UX purposes only.

Usage:
    DATABASE_URL=postgresql://... python database/seed.py

Idempotent: skips a table if it already has rows, so re-running is safe.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db import DB_ENABLED, SessionLocal, engine  # noqa: E402


def _seed_ideas(db, models):
    if db.query(models.IdeaBankEntry).count() > 0:
        print("idea_bank_entries: already seeded, skipping")
        return
    rows = [
        dict(
            title_en="Cloud kitchen for healthy meal subscriptions",
            title_ar="مطبخ سحابي لاشتراكات الوجبات الصحية",
            industry="retail",
            summary_en="Delivery-only kitchen serving weekly meal-prep subscriptions in major Saudi cities.",
            summary_ar="مطبخ توصيل فقط يقدّم اشتراكات وجبات أسبوعية في المدن السعودية الكبرى.",
            revenue_model="Subscription",
            investment_min=150000,
            investment_max=400000,
            difficulty="medium",
            status="published",
        ),
        dict(
            title_en="AI-assisted Arabic document OCR for SMEs",
            title_ar="استخراج نصوص عربية بالذكاء الاصطناعي للمنشآت الصغيرة",
            industry="technology",
            summary_en="SaaS tool digitizing scanned Arabic invoices/contracts for small businesses.",
            summary_ar="أداة SaaS لرقمنة الفواتير والعقود العربية الممسوحة ضوئيًا للمنشآت الصغيرة.",
            revenue_model="SaaS subscription",
            investment_min=80000,
            investment_max=250000,
            difficulty="high",
            status="published",
        ),
        dict(
            title_en="Modular eco-tourism camps in AlUla region",
            title_ar="مخيمات سياحة بيئية معيارية في منطقة العلا",
            industry="tourism",
            summary_en="Prefab eco-lodges targeting Vision 2030 domestic tourism growth.",
            summary_ar="نُزل بيئية جاهزة تستهدف نمو السياحة الداخلية ضمن رؤية 2030.",
            revenue_model="Nightly bookings",
            investment_min=500000,
            investment_max=2000000,
            difficulty="high",
            status="published",
        ),
    ]
    for r in rows:
        db.add(models.IdeaBankEntry(**r))
    db.commit()
    print("idea_bank_entries: seeded", len(rows))


def _seed_franchises(db, models):
    if db.query(models.FranchiseOpportunity).count() > 0:
        print("franchise_opportunities: already seeded, skipping")
        return
    rows = [
        dict(
            brand="Regional Specialty Coffee Co.",
            description_en="Illustrative example franchise listing -- not a real offer. Specialty coffee chain expanding into secondary Saudi cities.",
            description_ar="مثال توضيحي غير حقيقي — امتياز سلسلة قهوة مختصة يتوسع في مدن سعودية ثانوية.",
            sector="retail",
            country="Saudi Arabia",
            investment_min=300000,
            investment_max=900000,
            franchise_fee=60000,
            royalty_model="6% of gross monthly revenue",
            required_space="80-150 sqm",
            verification_status="demo",
        ),
        dict(
            brand="FitZone Boutique Studios",
            description_en="Illustrative example franchise listing -- not a real offer. Boutique fitness studio format.",
            description_ar="مثال توضيحي غير حقيقي — نموذج استوديو لياقة بدنية بوتيكي.",
            sector="tourism",
            country="Saudi Arabia",
            investment_min=200000,
            investment_max=600000,
            franchise_fee=40000,
            royalty_model="8% of gross monthly revenue",
            required_space="150-250 sqm",
            verification_status="demo",
        ),
    ]
    for r in rows:
        db.add(models.FranchiseOpportunity(**r))
    db.commit()
    print("franchise_opportunities: seeded", len(rows))


def _seed_auctions(db, models):
    if db.query(models.Auction).count() > 0:
        print("auctions: already seeded, skipping")
        return
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    rows = [
        dict(
            title="Established e-commerce storefront (illustrative example)",
            category="technology",
            description="Not a real listing -- example only. 3-year-old online retail business, profitable, seller retiring.",
            asking_price=650000,
            reserve_price=500000,
            starts_at=now,
            ends_at=now + timedelta(days=30),
            status="open",
        ),
        dict(
            title="Neighborhood pharmacy license + fit-out (illustrative example)",
            category="healthcare",
            description="Not a real listing -- example only. Licensed pharmacy location with existing fit-out for sale.",
            asking_price=1200000,
            reserve_price=950000,
            starts_at=now,
            ends_at=now + timedelta(days=45),
            status="open",
        ),
    ]
    for r in rows:
        db.add(models.Auction(**r))
    db.commit()
    print("auctions: seeded", len(rows))


def _seed_opportunities(db, models):
    if db.query(models.InvestmentOpportunity).count() > 0:
        print("investment_opportunities: already seeded, skipping")
        return
    rows = [
        dict(
            title_en="Logistics micro-fulfillment network (illustrative example)",
            title_ar="شبكة تلبية طلبات لوجستية صغيرة (مثال توضيحي)",
            industry="industrial",
            summary_en="Not a real offering -- example only. Last-mile micro-fulfillment nodes for e-commerce sellers in Riyadh/Jeddah.",
            summary_ar="ليس عرضًا حقيقيًا — مثال فقط. عُقد تلبية طلبات صغيرة للتجارة الإلكترونية في الرياض وجدة.",
            stage="early_revenue",
            risk_level="medium",
            investment_min=100000,
            investment_max=500000,
            expected_return_percent=18,
            funding_goal=1500000,
            funding_committed=450000,
            verification_status="demo",
        ),
        dict(
            title_en="Telehealth platform for rural clinics (illustrative example)",
            title_ar="منصة طب عن بُعد للعيادات الريفية (مثال توضيحي)",
            industry="healthcare",
            summary_en="Not a real offering -- example only. Video-consultation platform connecting rural clinics to specialists.",
            summary_ar="ليس عرضًا حقيقيًا — مثال فقط. منصة استشارات مرئية تربط العيادات الريفية بالأخصائيين.",
            stage="mvp",
            risk_level="high",
            investment_min=50000,
            investment_max=200000,
            expected_return_percent=25,
            funding_goal=800000,
            funding_committed=120000,
            verification_status="demo",
        ),
        dict(
            title_en="Boutique eco-resort, Red Sea coast (illustrative example)",
            title_ar="منتجع بيئي بوتيكي على ساحل البحر الأحمر (مثال توضيحي)",
            industry="tourism",
            summary_en="Not a real offering -- example only. Small-footprint eco-resort targeting domestic tourism demand.",
            summary_ar="ليس عرضًا حقيقيًا — مثال فقط. منتجع بيئي صغير يستهدف الطلب على السياحة الداخلية.",
            stage="growth",
            risk_level="low",
            investment_min=1000000,
            investment_max=5000000,
            expected_return_percent=12,
            funding_goal=8000000,
            funding_committed=6200000,
            verification_status="demo",
        ),
    ]
    for r in rows:
        db.add(models.InvestmentOpportunity(**r))
    db.commit()
    print("investment_opportunities: seeded", len(rows))


def main() -> None:
    if not DB_ENABLED:
        print("DATABASE_URL/POSTGRES_URL not set -- nothing to seed (demo/in-memory mode).")
        return
    from app import models  # noqa: F401  (register tables)

    db = SessionLocal()
    try:
        _seed_ideas(db, models)
        _seed_franchises(db, models)
        _seed_auctions(db, models)
        _seed_opportunities(db, models)
    finally:
        db.close()


if __name__ == "__main__":
    main()
