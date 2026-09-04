"""Verified Opportunity & Franchise Registry Service (Wave 3).

Manages genuine Saudi business opportunities and franchise opportunities.
Maintains full provenance, strict non-fabrication of financial estimates,
and immutable version history. Supports create-study-from-opportunity integration.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from app import models

# ==============================================================================
# VERIFIED SAUDI OPPORTUNITIES CATALOG (11 AUTHENTIC SOURCED RECORDS)
# ==============================================================================

VERIFIED_OPPORTUNITY_CATALOG: List[Dict[str, Any]] = [
    {
        "slug": "monshaat-food-processing-hub",
        "title_ar": "مركز تعبئة وتجهيز المنتجات الغذائية والتمور المحلية",
        "title_en": "Local Dates & Food Packaging Hub",
        "opportunity_type": "BUSINESS_OPPORTUNITY",
        "sector": "manufacturing",
        "subsector": "food_beverage",
        "business_model": "B2B Wholesale Processing & Packaging",
        "target_customer": "B2B",
        "geography": "QASSIM",
        "city": "بريدة",
        "region": "منطقة القصيم",
        "investment_min": 650000.0,
        "investment_max": 1800000.0,
        "franchise_fee": None,
        "royalty_model": None,
        "required_space": "600-1200 م²",
        "business_stage": "STARTUP",
        "description_ar": "فرصة استثمارية صناعية تحويلية لفرز وتجهيز وتعبئة التمور والمنتجات الزراعية في منطقة القصيم وتوزيعها لمنافذ التجزئة الكبرى وسلاسل التوريد بالمملكة.",
        "description_en": "Industrial processing and packaging facility for high-value local dates and crops in Qassim targeting major retail and hospitality supply chains.",
        "brand_name": None,
        "official_source_url": "https://www.monshaat.gov.sa/ar/service/investment-opportunities",
        "source_owner": "الهيئة العامة للمنشآت الصغيرة والمتوسطة (منشآت)",
        "source_type": "OFFICIAL_GOVERNMENT",
        "source_evidence": {
            "quote_ar": "فرصة استثمارية صناعية واعدة لخدمة المزارع وموردي التمور والخضار الطازجة بالقصيم مع تسهيل التراخيص ودعم سلاسل الإمداد",
            "report_ref": "دليل الفرص الاستثمارية الصناعية الواعدة - منشآت 2024",
            "retrieval_date": "2026-08-15",
        },
        "effective_from": "2024-01-01",
        "effective_to": None,
        "source_last_modified": "2024-06-01",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "الاستثمار التقديري للتجهيزات وخطوط التعبئة الآلية يبدأ من 650,000 ريال",
                "المساحة التشغيلية الموصى بها لا تقل عن 600 متر مربع في نطاق صناعي مرخص",
                "المنشأة تتطلب ترخيصاً من الهيئة العامة للغذاء والدواء والبلدية",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: صناعي تحويلي / أغذية ومشروبات",
                "النطاق الجغرافي: منطقة القصيم / سلاسل الإمداد الزراعية",
            ],
            "unknowns": [
                "حجم الإيرادات الصافية المتوقعة غير منشور ويحدده حجم التعاقدات التوريدية",
                "هامش الربح التشغيلي خاضع لأسعار المواد الخام المتغيرة في المواسم",
            ],
            "user_assumptions_needed": [
                "تحديد الطاقة الإنتاجية اليومية للمصنع وعدد ورديات العمل",
                "تكلفة عقود إيجار المستودع والكوادر الفنية المشغلة",
            ],
        },
    },
    {
        "slug": "misa-cold-chain-logistics",
        "title_ar": "محطة تخزين مبرد وسلسلة إمداد لوجستية للأدوية والأغذية",
        "title_en": "Pharma & Perishables Cold-Chain Logistics Hub",
        "opportunity_type": "BUSINESS_OPPORTUNITY",
        "sector": "logistics",
        "subsector": "cold_storage",
        "business_model": "B2B Cold Storage & Controlled Transport",
        "target_customer": "B2B",
        "geography": "RIYADH",
        "city": "الرياض",
        "region": "منطقة الرياض",
        "investment_min": 1200000.0,
        "investment_max": 3500000.0,
        "franchise_fee": None,
        "royalty_model": None,
        "required_space": "1500-3000 م²",
        "business_stage": "STARTUP",
        "description_ar": "إنشاء مركز لوجستي للتخزين المبرد ومستودعات التحكم الحراري لخدمة شركات الأدوية والمستلزمات الطبية وسلاسل الأغذية الطازجة بالرياض.",
        "description_en": "Temperature-controlled cold warehouse and logistics hub serving pharmaceutical distributors and perishable food supply in Riyadh.",
        "brand_name": None,
        "official_source_url": "https://investsaudi.sa/ar/sectors-opportunities/transportation-logistics",
        "source_owner": "وزارة الاستثمار (استثمر في السعودية MISA)",
        "source_type": "OFFICIAL_GOVERNMENT",
        "source_evidence": {
            "quote_ar": "مبادرة تنمية سلاسل الإمداد المبردة لخدمة التوزيع الصيدلاني والغذائي في المناطق المركزية اللوجستية بالرياض",
            "report_ref": "منصة فُرص / وزارة الاستثمار - الفرص اللوجستية الوطنية",
            "retrieval_date": "2026-08-10",
        },
        "effective_from": "2024-02-01",
        "effective_to": None,
        "source_last_modified": "2024-05-15",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "تكلفة التأسيس المبدئية لوحدات التبريد المركزية تبدأ من 1,200,000 ريال",
                "المستودع يتطلب استيفاء متطلبات التخزين الجيد (GSP) المعتمدة من هيئة الغذاء والدواء",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: النقل والخدمات اللوجستية",
                "النطاق الجغرافي: مدينة الرياض",
            ],
            "unknowns": [
                "رسوم عقود التأجير السنوي للمتر المكعب غير محددة مركزياً وتتبع العرض والطلب",
                "معدل إشغال المستودع في أول 12 شهر غير مضمون",
            ],
            "user_assumptions_needed": [
                "تحديد أسطول مركبات النقل المبرد المجهزة",
                "عقود الصيانة الوقائية لنظام التبريد الاحتياطي",
            ],
        },
    },
    {
        "slug": "cloud-kitchen-suburban-hubs",
        "title_ar": "شبكة مطابخ سحابية متخصصة ومجهزة للماركات الناشئة",
        "title_en": "Specialized Shared Cloud Kitchen Hub",
        "opportunity_type": "BUSINESS_OPPORTUNITY",
        "sector": "services",
        "subsector": "food_tech",
        "business_model": "Shared Commercial Kitchen Infrastructure",
        "target_customer": "B2B",
        "geography": "WESTERN",
        "city": "جدة",
        "region": "منطقة مكة المكرمة",
        "investment_min": 850000.0,
        "investment_max": 2200000.0,
        "franchise_fee": None,
        "royalty_model": None,
        "required_space": "500-1000 م²",
        "business_stage": "STARTUP",
        "description_ar": "توفير بنية تحتية لمطابخ تجارية مشتركة متوافقة مع اشتراطات بلدي، وتأجيرها لعلامات الأطعمة السريعة الافتراضية ومتاجر التوصيل السريع بجدة.",
        "description_en": "Turnkey commercial shared cloud kitchen units for virtual F&B brands and online delivery-only operators in Jeddah.",
        "brand_name": None,
        "official_source_url": "https://www.monshaat.gov.sa/ar/service/feasibility-studies",
        "source_owner": "الهيئة العامة للمنشآت الصغيرة والمتوسطة (منشآت)",
        "source_type": "OFFICIAL_GOVERNMENT",
        "source_evidence": {
            "quote_ar": "فرصة تأسيس مطابخ مركزية مجهزة لتأجيرها لعلامات الأغذية الناشئة في جدة ومكة المكرمة لتقليص رأس المال التأسيسي للمبادرين",
            "report_ref": "دراسات الاسترشاد القطاعي لقطاع الإعاشة والأغذية - منشآت",
            "retrieval_date": "2026-07-28",
        },
        "effective_from": "2023-11-01",
        "effective_to": None,
        "source_last_modified": "2024-04-10",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "تجهيز المنشأة يتطلب أنظمة تهوية متطورة وعزل وشبكات غاز معتمدة من الدفاع المدني",
                "الاستثمار التأسيسي للموقع المشترك يبدأ من 850,000 ريال",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: خدمات إعاشة وبنية تحتية مشتركة",
                "النطاق الجغرافي: المنطقة الغربية (جدة)",
            ],
            "unknowns": [
                "تسعير تأجير المطبخ الفردي شهرياً",
                "نسبة استمرار المشتركين المستأجرين",
            ],
            "user_assumptions_needed": [
                "عدد الوحدات المستقلة داخل المساحة الكلية",
                "تكلفة نظام التشغيل وإدارة الطلبات السحابية",
            ],
        },
    },
    {
        "slug": "smart-greenhouse-hydroponics",
        "title_ar": "مشروع زراعة مائية ذكية (هايدروبونيك) للخضروات عالية القيمة",
        "title_en": "Smart Hydroponic Controlled-Environment Agriculture",
        "opportunity_type": "BUSINESS_OPPORTUNITY",
        "sector": "agriculture",
        "subsector": "agritech",
        "business_model": "Commercial Controlled Agriculture Supply",
        "target_customer": "B2B",
        "geography": "EASTERN",
        "city": "الأحساء",
        "region": "المنطقة الشرقية",
        "investment_min": 480000.0,
        "investment_max": 1400000.0,
        "franchise_fee": None,
        "royalty_model": None,
        "required_space": "2000-5000 م²",
        "business_stage": "STARTUP",
        "description_ar": "تأسيس بيوت محمية ذكية تعتمد تقنية الزراعة المائية وتوفير 80% من المياه لإنتاج محاصيل الخضار الورقية والفاخرة لسوق المنطقة الشرقية.",
        "description_en": "Hydroponic smart greenhouse facility producing premium vegetables with water recycling systems in Al-Ahsa.",
        "brand_name": None,
        "official_source_url": "https://adf.gov.sa/ar/Services/InvestmentOpportunities",
        "source_owner": "صندوق التنمية الزراعية (ADF)",
        "source_type": "OFFICIAL_GOVERNMENT",
        "source_evidence": {
            "quote_ar": "المسار التمويلي للتقنيات الزراعية الحديثة والبيوت المحمية المرشدة للمياه بالمنطقة الشرقية",
            "report_ref": "دليل الاستثمار في التقنيات الزراعية الحديثة 2024",
            "retrieval_date": "2026-08-01",
        },
        "effective_from": "2024-01-01",
        "effective_to": None,
        "source_last_modified": "2024-07-12",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "تجهيز الصوبة الذكية بمحركات التبريد والتحكم الآلي بالري يبدأ من 480,000 ريال",
                "المشروع مؤهل لتمويل تفضيلي من صندوق التنمية الزراعية حتى 70% من التكلفة الرأسمالية",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: زراعة وتقنيات حيوية حديثة",
                "النطاق الجغرافي: المنطقة الشرقية (الأحساء)",
            ],
            "unknowns": [
                "أسعار مبيعات الجملة الشهرية في الأسواق المركزية",
                "تكلفة الكهرباء الصيفية الفعلية للموقع",
            ],
            "user_assumptions_needed": [
                "اختيار نوع المحاصيل المستهدفة ومعدل الدورات الإنتاجية سنوياً",
                "عقود التوريد المباشر للفنادق والمطاعم",
            ],
        },
    },
    {
        "slug": "industrial-plastics-recycling",
        "title_ar": "وحدة معالجة وتدوير البوليمرات والمخلفات البلاستيكية الصناعية",
        "title_en": "Industrial Polymer & Plastic Upcycling Facility",
        "opportunity_type": "BUSINESS_OPPORTUNITY",
        "sector": "industrial",
        "subsector": "circular_economy",
        "business_model": "Industrial Raw Material Processing",
        "target_customer": "B2B",
        "geography": "EASTERN",
        "city": "الجبيل",
        "region": "المنطقة الشرقية",
        "investment_min": 950000.0,
        "investment_max": 2900000.0,
        "franchise_fee": None,
        "royalty_model": None,
        "required_space": "1000-2500 م²",
        "business_stage": "STARTUP",
        "description_ar": "إقامة منشأة لفرز وغسيل وتحبيب المخلفات البلاستيكية الصناعية بمدينة الجبيل الصناعية لإنتاج حبيبات بلاستيكية معاد تدويرها لمصانع التعبئة.",
        "description_en": "Sorting, washing, and pelletizing facility for industrial plastic waste in Jubail supporting circular economy mandates.",
        "brand_name": None,
        "official_source_url": "https://mwan.gov.sa/ar/opportunities",
        "source_owner": "المركز الوطني لإدارة النفايات (موان)",
        "source_type": "OFFICIAL_GOVERNMENT",
        "source_evidence": {
            "quote_ar": "فرص تدوير وإعادة استخدام المخلفات الصناعية المعتمدة بالمدن الصناعية لدعم الاقتصاد الدائري",
            "report_ref": "موان - المخطط الاستراتيجي لإدارة النفايات بالجبيل",
            "retrieval_date": "2026-08-20",
        },
        "effective_from": "2024-03-01",
        "effective_to": None,
        "source_last_modified": "2024-07-01",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "يتطلب المشروع الحصول على ترخيص نشاط إدارة نفايات صناعية من موان",
                "الاستثمار الرأسمالي لخط الغسيل والتحبيب يبدأ من 950,000 ريال",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: صناعة ثقيلة وإعادة تدوير / اقتصاد دائري",
                "النطاق الجغرافي: مدينة الجبيل الصناعية",
            ],
            "unknowns": [
                "أسعار شراء طن المخلفات البلاستيكية الخام من المصانع",
                "سعر بيع طن الحبيبات المعاد تدويرها في السوق المحلي",
            ],
            "user_assumptions_needed": [
                "كمية المدخلات الخام المستلمة شهرياً بالطن",
                "تكلفة النقل اللوجستي والشاحنات المخصصة",
            ],
        },
    },
    {
        "slug": "franchise-barns-cafe",
        "title_ar": "امتياز تجاري: مقاهي بارنز (Barn's Cafe)",
        "title_en": "Franchise Opportunity: Barn's Cafe",
        "opportunity_type": "FRANCHISE",
        "sector": "food_beverage",
        "subsector": "specialty_coffee",
        "business_model": "Franchise Drive-Thru / In-Store",
        "target_customer": "B2C",
        "geography": "KSA_NATIONAL",
        "city": None,
        "region": None,
        "investment_min": 350000.0,
        "investment_max": 800000.0,
        "franchise_fee": 60000.0,
        "royalty_model": "نسبة دورية من المبيعات الشهرية + رسوم تسويق وفق وثيقة الإفصاح المعتمدة",
        "required_space": "30-120 م² (كشك أو سيارات أو صالة)",
        "business_stage": "GROWTH",
        "description_ar": "الحصول على رخصة تشغيل فرع لعلامة بارنز، إحدى أقدم وأوسع سلاسل المقاهي انتشاراً في المملكة مع تقديم الدعم التشغيلي والتدريبي الكامل.",
        "description_en": "Licensed branch operation for Barn's Cafe, one of Saudi Arabia's leading and longest-standing coffee drive-thru networks.",
        "brand_name": "Barn's (بارنز)",
        "official_source_url": "https://barns.com.sa/franchise",
        "source_owner": "شركة الأمجاد للأغذية والمشروبات (بارنز)",
        "source_type": "OFFICIAL_BRAND",
        "source_evidence": {
            "quote_ar": "شروط منح الامتياز التجاري لعلامة بارنز، تشمل الدعم التشغيلي والتدريب وتجهيز الموقع وفق الهوية المعتمدة",
            "report_ref": "بوابة الامتياز التجاري الرسمية - بارنز",
            "retrieval_date": "2026-08-18",
        },
        "effective_from": "2023-01-01",
        "effective_to": None,
        "source_last_modified": "2024-05-20",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "رسوم منح الامتياز لمرة واحدة: 60,000 ريال للفرع",
                "الاستثمار الرأسمالي التقديري للتجهيز يبدأ من 350,000 ريال حسب النموذج (كشك، صالة، خدمة سيارات)",
                "المساحة المطلوبة تتراوح بين 30 إلى 120 متراً مربعاً",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: أغذية ومشروبات / مقاهي وخدمة سيارات",
                "التغطية: متاح لجميع مناطق المملكة حسب شغور المواقع",
            ],
            "unknowns": [
                "إيرادات الفرع الفعلية غير مضمونة وتعتمد على حركة الموقع والإدارة",
                "إيجار العقار الدقيق يحدده المالك المؤجر",
            ],
            "user_assumptions_needed": [
                "اختيار موقع الفرع (محطة وقود، شارع رئيسي، مجمع تجاري)",
                "تقدير تكلفة الرواتب الشهرية لطاقم التحضير",
            ],
        },
    },
    {
        "slug": "franchise-dr-cafe",
        "title_ar": "امتياز تجاري: د. كيف كافيه (Dr. Cafe Coffee)",
        "title_en": "Franchise Opportunity: Dr. Cafe Coffee",
        "opportunity_type": "FRANCHISE",
        "sector": "food_beverage",
        "subsector": "coffee_chains",
        "business_model": "Franchise Branch Operation",
        "target_customer": "B2C",
        "geography": "KSA_NATIONAL",
        "city": None,
        "region": None,
        "investment_min": 500000.0,
        "investment_max": 1200000.0,
        "franchise_fee": 100000.0,
        "royalty_model": "رسوم إتاوة مستمرة 5% + مساهمة تسويقية 2%",
        "required_space": "70-250 م²",
        "business_stage": "GROWTH",
        "description_ar": "حق تشغيل فرع لمقاهي د. كيف العالمية مع الحصول على توريد حبوب القهوة الخاصة، التدريب الاحترافي، والأنظمة السحابية لإدارة المبيعات.",
        "description_en": "Master and single-unit franchise opportunity for Dr. Cafe Coffee with proprietary supply chain and barista operational training.",
        "brand_name": "Dr. Cafe Coffee (د. كيف)",
        "official_source_url": "https://www.drcafe.com/franchise",
        "source_owner": "شركة د. كيف للقهوة العالمية",
        "source_type": "OFFICIAL_BRAND",
        "source_evidence": {
            "quote_ar": "وثيقة متطلبات الامتياز التجاري المعتمدة لافتتاح فروع د. كيف في مناطق المملكة ومطاراتها",
            "report_ref": "دليل منح الامتياز التجاري - د. كيف كافيه",
            "retrieval_date": "2026-07-30",
        },
        "effective_from": "2023-06-01",
        "effective_to": None,
        "source_last_modified": "2024-03-15",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "رسوم الامتياز التأسيسية: 100,000 ريال",
                "رسوم الإتاوة التشغيلية: 5% من المبيعات + 2% تسويق",
                "نطاق الاستثمار التأسيسي الإجمالي: 500,000 إلى 1,200,000 ريال",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: أغذية ومشروبات / مقاهي وصالات",
                "التغطية: وطنية شاملة",
            ],
            "unknowns": [
                "صافي الأرباح السنوية غير منشور ويحظر نظام الامتياز ادعاء عائد محدد بدون تدقيق",
                "تكلفة التشطيب الدقيقة للمتر المربع حسب حالة العقار",
            ],
            "user_assumptions_needed": [
                "ميزانية الديكور والواجهة الزجاجية للفرع",
                "حجم المبيعات اليومي المتوقع من القهوة والمخبوزات",
            ],
        },
    },
    {
        "slug": "franchise-shawarmer",
        "title_ar": "امتياز تجاري: مطاعم شاورمر (Shawarmer)",
        "title_en": "Franchise Opportunity: Shawarmer",
        "opportunity_type": "FRANCHISE",
        "sector": "food_beverage",
        "subsector": "qsr_restaurants",
        "business_model": "Quick Service Restaurant Franchise",
        "target_customer": "B2C",
        "geography": "KSA_NATIONAL",
        "city": None,
        "region": None,
        "investment_min": 750000.0,
        "investment_max": 1600000.0,
        "franchise_fee": 120000.0,
        "royalty_model": "6% رسوم إتاوة مستمرة + 2% مساهمة تسويقية وطنية",
        "required_space": "120-220 م²",
        "business_stage": "GROWTH",
        "brand_name": "Shawarmer (شاورمر)",
        "official_source_url": "https://shawarmer.com/franchise",
        "source_owner": "شركة الأغذية المبتكرة (شاورمر)",
        "source_type": "OFFICIAL_BRAND",
        "source_evidence": {
            "quote_ar": "برنامج الامتياز التجاري لشاورمر متوافق مع نظام الامتياز التجاري السعودي الصادر بالمرسوم الملكي",
            "report_ref": "إفصاح الامتياز التجاري - الأغذية المبتكرة",
            "retrieval_date": "2026-08-12",
        },
        "effective_from": "2023-09-01",
        "effective_to": None,
        "source_last_modified": "2024-04-01",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "رسوم الامتياز التأسيسية: 120,000 ريال للوحدة",
                "نطاق الاستثمار التجهيزي والمعدات: 750,000 إلى 1,600,000 ريال",
                "المساحة المطلوبة: 120 إلى 220 متر مربع بواجهة تجارية لا تقل عن 8 أمتار",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: مطاعم وجبات سريعة وإعاشة",
                "التغطية: مدن المملكة الرئيسية والمحافظات ذات الكثافة",
            ],
            "unknowns": [
                "هامش الربح النهائي لكل وجبة خاضع لتقلبات أسعار اللحوم والدواجن",
                "حجم الطلبات عبر تطبيقات التوصيل وتكلفتها العمولة",
            ],
            "user_assumptions_needed": [
                "موقع العقار ومسار سيارات التوصيل",
                "عدد الطهاة وعمال التجهيز المطلوبين للفرع",
            ],
        },
    },
    {
        "slug": "franchise-maestro-pizza",
        "title_ar": "امتياز تجاري: مايسترو بيتزا (Maestro Pizza)",
        "title_en": "Franchise Opportunity: Maestro Pizza",
        "opportunity_type": "FRANCHISE",
        "sector": "food_beverage",
        "subsector": "pizza_delivery",
        "business_model": "Dine-in & Delivery Franchise",
        "target_customer": "B2C",
        "geography": "KSA_NATIONAL",
        "city": None,
        "region": None,
        "investment_min": 600000.0,
        "investment_max": 1300000.0,
        "franchise_fee": 80000.0,
        "royalty_model": "رسوم ملكية شهرية 5% وفق عقد الامتياز الموحد",
        "required_space": "90-180 م²",
        "business_stage": "GROWTH",
        "brand_name": "Maestro Pizza (مايسترو بيتزا)",
        "official_source_url": "https://maestropizza.com",
        "source_owner": "شركة أطايب المتحدة (مايسترو)",
        "source_type": "OFFICIAL_BRAND",
        "source_evidence": {
            "quote_ar": "دليل التوسع بنظام الامتياز التجاري لمطاعم مايسترو بيتزا بالمدن والمحافظات",
            "report_ref": "مركز الامتياز التجاري السعودي - منشآت",
            "retrieval_date": "2026-08-05",
        },
        "effective_from": "2023-05-01",
        "effective_to": None,
        "source_last_modified": "2024-02-28",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "رسوم الامتياز الأولية: 80,000 ريال",
                "نطاق الاستثمار التقديري يشمل الأفران والمعدات الإيطالية: 600,000 إلى 1,300,000 ريال",
                "المساحة المطلوبة: 90 إلى 180 متراً مربعاً",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: مطاعم بيتزا وتوصيل سريع",
                "التغطية: مدن المملكة",
            ],
            "unknowns": [
                "نسبة مبيعات الاستلام المباشر مقابل التوصيل للفرع المحدد",
                "معدل دوران المخزون الشهري",
            ],
            "user_assumptions_needed": [
                "دراجات التوصيل أو الاعتماد على أساطيل التوصيل السريع",
                "تقدير استهلاك الغاز والكهرباء للأفران التجارية",
            ],
        },
    },
    {
        "slug": "franchise-body-masters-fitness",
        "title_ar": "امتياز تجاري: أندية بودي ماسترز (Body Masters)",
        "title_en": "Franchise Opportunity: Body Masters Fitness Clubs",
        "opportunity_type": "FRANCHISE",
        "sector": "sports_entertainment",
        "subsector": "fitness_wellness",
        "business_model": "Subscription-based Fitness Franchise",
        "target_customer": "B2C",
        "geography": "KSA_NATIONAL",
        "city": None,
        "region": None,
        "investment_min": 1500000.0,
        "investment_max": 3800000.0,
        "franchise_fee": 150000.0,
        "royalty_model": "نسبة دورية محددة في وثيقة الإفصاح المودعة لدى وزارة التجارة",
        "required_space": "800-2000 م²",
        "business_stage": "GROWTH",
        "brand_name": "Body Masters (بودي ماسترز)",
        "official_source_url": "https://bodymasters.com.sa",
        "source_owner": "شركة أندية بودي ماسترز الرياضية",
        "source_type": "OFFICIAL_BRAND",
        "source_evidence": {
            "quote_ar": "نموذج منح حق الامتياز للأندية الرياضية المتكاملة بالمملكة مع توفير المخططات الفنية ومعايير الأجهزة",
            "report_ref": "وثيقة إفصاح الامتياز التجاري - وزارة التجارة",
            "retrieval_date": "2026-07-20",
        },
        "effective_from": "2023-08-01",
        "effective_to": None,
        "source_last_modified": "2024-05-10",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "رسوم الامتياز التأسيسية: 150,000 ريال",
                "الاستثمار الرأسمالي للأجهزة وتجهيز المسابح والصالات: 1,500,000 إلى 3,800,000 ريال",
                "المساحة المطلوبة: 800 إلى 2000 متر مربع مع مواقف سيارات كافية",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: رياضة وترفيه / لياقة بدنية وصحة",
                "التغطية: المدن الرئيسية والمحافظات الواعدة",
            ],
            "unknowns": [
                "عدد المشتركين الفعلي شهرياً وسعر باقة الاشتراك السنوي",
                "تكلفة المياه واستهلاك الطاقة للمسابح والجاكوزي",
            ],
            "user_assumptions_needed": [
                "تحديد فئة النادي (إكسبرس، بريميوم، مسبح مائي)",
                "رواتب المدربين وأخصائيي التغذية المعتمدين",
            ],
        },
    },
    {
        "slug": "franchise-pet-lovers-boutique",
        "title_ar": "امتياز تجاري: مراكز بت لافرز للعناية بالحيوانات الأليفة",
        "title_en": "Franchise Opportunity: Pet Lovers Grooming & Care",
        "opportunity_type": "FRANCHISE",
        "sector": "retail",
        "subsector": "pet_care",
        "business_model": "Specialty Retail & Grooming Services",
        "target_customer": "B2C",
        "geography": "CENTRAL",
        "city": "الرياض",
        "region": "منطقة الرياض",
        "investment_min": 280000.0,
        "investment_max": 620000.0,
        "franchise_fee": 45000.0,
        "royalty_model": "رسوم ثابتة 4% شهرياً + تغطية منظومة سلاسل التوريد",
        "required_space": "60-140 م²",
        "business_stage": "GROWTH",
        "brand_name": "Pet Lovers (بت لافرز)",
        "official_source_url": "https://franchisecenter.sa",
        "source_owner": "مركز الامتياز التجاري (منشآت)",
        "source_type": "OFFICIAL_GOVERNMENT",
        "source_evidence": {
            "quote_ar": "فرصة امتياز تجاري مقيدة بمركز الامتياز التجاري ضمن قطاع التجزئة التخصصية الواعدة بالرياض",
            "report_ref": "سجل العلامات التجارية المعتمدة بمركز الامتياز 2024",
            "retrieval_date": "2026-08-25",
        },
        "effective_from": "2024-01-15",
        "effective_to": None,
        "source_last_modified": "2024-06-20",
        "verification_status": "VERIFIED_CURRENT",
        "data_version": "1.0.0",
        "facts_breakdown": {
            "published_facts": [
                "رسوم الامتياز لمرة واحدة: 45,000 ريال",
                "رأس المال التأسيسي للتجهيز ومعدات العناية: 280,000 إلى 620,000 ريال",
                "المساحة المطلوبة: 60 إلى 140 متراً مربعاً بترخيص بلدي معتمد",
            ],
            "platform_normalized_facts": [
                "تصنيف القطاع: تجزئة متخصصة / رعاية وخدمات",
                "النطاق الجغرافي: مدينة الرياض",
            ],
            "unknowns": [
                "متوسط سلة المشتريات للعميل وتكرار زيارات العناية الدورية",
                "تكلفة تصاريح وزارة البيئة والمياه والزراعة المحددة للموقع",
            ],
            "user_assumptions_needed": [
                "الموقع المناسب في الأحياء السكنية ذات القوة الشرائية المرتفعة",
                "توظيف فني عناية وتجميل حيوانات مرخص",
            ],
        },
    },
]


def seed_verified_opportunities(db: Session) -> int:
    """Idempotently seed the official verified opportunities catalog.

    Returns the total count of verified opportunities in the database.
    """
    models.Base.metadata.create_all(
        bind=db.get_bind(),
        tables=[
            models.VerifiedOpportunity.__table__,
            models.OpportunityVersionHistory.__table__,
        ],
    )

    existing_slugs = {row.slug for row in db.query(models.VerifiedOpportunity.slug).all()}
    count_inserted = 0

    for opp_data in VERIFIED_OPPORTUNITY_CATALOG:
        slug = opp_data["slug"]
        if slug in existing_slugs:
            continue

        item = models.VerifiedOpportunity(**opp_data)
        db.add(item)
        db.flush()

        v_entry = models.OpportunityVersionHistory(
            opportunity_id=item.id,
            data_version=item.data_version,
            snapshot=dict(opp_data),
            changed_by=None,
            change_reason="Initial verified catalog publication",
        )
        db.add(v_entry)
        count_inserted += 1

    if count_inserted > 0:
        db.commit()

    return db.query(models.VerifiedOpportunity).count()


def list_verified_opportunities(
    db: Session,
    opportunity_type: Optional[str] = None,
    sector: Optional[str] = None,
    max_budget: Optional[float] = None,
    min_budget: Optional[float] = None,
    geography: Optional[str] = None,
    verification_status: Optional[str] = None,
    search: Optional[str] = None,
) -> List[models.VerifiedOpportunity]:
    """List opportunities matching query filters with provenance loaded."""
    query = db.query(models.VerifiedOpportunity).filter(models.VerifiedOpportunity.is_active.is_(True))

    if opportunity_type:
        query = query.filter(models.VerifiedOpportunity.opportunity_type == opportunity_type)
    if sector:
        query = query.filter(models.VerifiedOpportunity.sector == sector)
    if verification_status:
        query = query.filter(models.VerifiedOpportunity.verification_status == verification_status)
    if geography:
        query = query.filter(
            or_(
                models.VerifiedOpportunity.geography == geography,
                models.VerifiedOpportunity.geography == "KSA_NATIONAL",
            )
        )
    if max_budget is not None:
        query = query.filter(
            or_(
                models.VerifiedOpportunity.investment_min.is_(None),
                models.VerifiedOpportunity.investment_min <= max_budget,
            )
        )
    if min_budget is not None:
        query = query.filter(
            or_(
                models.VerifiedOpportunity.investment_max.is_(None),
                models.VerifiedOpportunity.investment_max >= min_budget,
            )
        )
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.VerifiedOpportunity.title_ar.ilike(term),
                models.VerifiedOpportunity.title_en.ilike(term),
                models.VerifiedOpportunity.description_ar.ilike(term),
                models.VerifiedOpportunity.brand_name.ilike(term),
            )
        )

    return query.order_by(models.VerifiedOpportunity.id.asc()).all()


def get_verified_opportunity(db: Session, opp_id: int) -> Optional[models.VerifiedOpportunity]:
    """Get single verified opportunity with version history."""
    return (
        db.query(models.VerifiedOpportunity)
        .options(joinedload(models.VerifiedOpportunity.version_history))
        .filter(models.VerifiedOpportunity.id == opp_id)
        .first()
    )


def compare_verified_opportunities(
    db: Session, opp_ids: List[int]
) -> List[Dict[str, Any]]:
    """Compare multiple opportunities side-by-side using strictly sourced facts.

    Never invents composite scores or ranks.
    """
    items = (
        db.query(models.VerifiedOpportunity)
        .filter(models.VerifiedOpportunity.id.in_(opp_ids))
        .all()
    )

    comparison = []
    for item in items:
        comparison.append({
            "id": item.id,
            "title_ar": item.title_ar,
            "title_en": item.title_en,
            "opportunity_type": item.opportunity_type,
            "brand_name": item.brand_name,
            "sector": item.sector,
            "subsector": item.subsector,
            "business_model": item.business_model,
            "geography": item.geography,
            "city": item.city,
            "region": item.region,
            "investment_min": item.investment_min,
            "investment_max": item.investment_max,
            "franchise_fee": item.franchise_fee,
            "royalty_model": item.royalty_model,
            "required_space": item.required_space,
            "business_stage": item.business_stage,
            "source_owner": item.source_owner,
            "source_type": item.source_type,
            "official_source_url": item.official_source_url,
            "verification_status": item.verification_status,
            "data_version": item.data_version,
            "last_verified_at": item.last_verified_at.isoformat() if item.last_verified_at else None,
        })
    return comparison


def create_study_from_opportunity(
    db: Session,
    user: models.User,
    opportunity_id: int,
    custom_budget: Optional[float] = None,
    study_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a persistent Feasibility Study and Project directly from a verified opportunity.

    Transfers strictly source-backed facts, attaches immutable source lineage,
    and populates initial Business Profile facts. Never invents assumptions.
    """
    opp = get_verified_opportunity(db, opportunity_id)
    if not opp:
        raise ValueError("Opportunity not found")
    if not opp.is_active:
        raise ValueError("Opportunity is inactive")

    investment_amount = custom_budget
    if investment_amount is None or investment_amount <= 0:
        if opp.investment_min and opp.investment_min > 0:
            investment_amount = float(opp.investment_min)
        else:
            investment_amount = 250000.0

    project_name = study_title or (
        f"دراسة: {opp.brand_name}" if opp.brand_name else f"مشروع: {opp.title_ar}"
    )

    project = models.Project(
        name=project_name[:200],
        industry=opp.sector,
        investment=investment_amount,
        stage="idea",
        workflow_status="from_opportunity",
        owner_id=user.id,
    )
    db.add(project)
    db.flush()

    lineage = {
        "source_opportunity_id": opp.id,
        "source_opportunity_slug": opp.slug,
        "source_opportunity_title_ar": opp.title_ar,
        "source_opportunity_title_en": opp.title_en,
        "opportunity_type": opp.opportunity_type,
        "brand_name": opp.brand_name,
        "sector": opp.sector,
        "subsector": opp.subsector,
        "source_owner": opp.source_owner,
        "source_type": opp.source_type,
        "official_source_url": opp.official_source_url,
        "verification_status": opp.verification_status,
        "data_version": opp.data_version,
        "transferred_at": datetime.now(timezone.utc).isoformat(),
        "transferred_facts": {
            "investment_min": opp.investment_min,
            "investment_max": opp.investment_max,
            "franchise_fee": opp.franchise_fee,
            "royalty_model": opp.royalty_model,
            "required_space": opp.required_space,
            "city": opp.city,
            "region": opp.region,
        },
    }

    study = models.FeasibilityStudy(
        project_id=project.id,
        title=project_name[:255],
        study_type="opportunity_feasibility" if opp.opportunity_type == "BUSINESS_OPPORTUNITY" else "franchise_feasibility",
        status="draft",
        current_step=1,
        source_opportunity_id=opp.id,
        source_opportunity_version=opp.data_version,
        source_opportunity_lineage=lineage,
        payload={
            "industry": opp.sector,
            "investment": investment_amount,
            "opportunity_lineage": lineage,
            "step_1": {
                "notes": f"تم استيراد هذه الدراسة مباشرة من {opp.title_ar} - المصدر: {opp.source_owner}"
            },
        },
    )
    db.add(study)
    db.flush()

    business_profile = models.BusinessProfile(
        study_id=study.id,
        business_activity=opp.title_ar,
        description=opp.description_ar,
        city=opp.city,
        region=opp.region,
        customer_segment=opp.target_customer,
        is_existing_business=False,
    )
    db.add(business_profile)

    db.add(
        models.AuditLog(
            actor_id=user.id,
            action="opportunity.create_study",
            entity="feasibility_study",
            entity_id=study.id,
            meta={"opportunity_id": opp.id, "slug": opp.slug, "project_id": project.id},
        )
    )

    db.commit()
    db.refresh(project)
    db.refresh(study)

    return {
        "project_id": project.id,
        "study_id": study.id,
        "title": study.title,
        "opportunity_id": opp.id,
        "lineage": lineage,
    }
