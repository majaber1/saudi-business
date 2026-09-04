"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getLaunchWorkspace,
  addLaunchMilestone,
  updateLaunchMilestone,
  recordLaunchActuals,
  createLaunchReforecast,
  type LaunchWorkspaceData,
  type LaunchMilestone,
  type LaunchActualPeriod,
  type LaunchVarianceReport,
  type LaunchVarianceSummary,
  type LaunchReforecast,
} from "@/lib/api";

const milestoneCategories = [
  { value: "CR_AND_LICENSING", ar: "السجل التجاري والتراخيص البلدية والقطاعية", en: "CR & Licensing" },
  { value: "LOCATION_FITOUT", ar: "تجهيز الموقع والتشطيبات والمعدات", en: "Location Fitout & Equipment" },
  { value: "STAFFING_QIWA", ar: "التوظيف والتعاقد ونسب التوطين (قوى)", en: "Staffing & Qiwa Platform" },
  { value: "POS_ZATCA", ar: "الربط التقني مع الفوترة الإلكترونية (زاتكا) ونقاط البيع", en: "POS & ZATCA Integration" },
  { value: "SUPPLY_CHAIN", ar: "عقود التوريد والمخزون وسلاسل الإمداد", en: "Supply Chain & Vendors" },
  { value: "MARKETING_PRELAUNCH", ar: "الحملة التسويقية والتسجيل المسبق", en: "Pre-launch Marketing" },
  { value: "COMMERCIAL_OPENING", ar: "الافتتاح التجاري والتشغيل الكامل", en: "Commercial Launch" },
];

const milestoneStatusMap: Record<string, { ar: string; badge: string }> = {
  PENDING: { ar: "قيد الانتظار", badge: "bg-slate-100 text-slate-700 border-slate-300" },
  IN_PROGRESS: { ar: "جارٍ التنفيذ", badge: "bg-blue-100 text-blue-700 border-blue-300" },
  COMPLETED: { ar: "مكتمل بنجاح", badge: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  BLOCKED: { ar: "معطل / متعثر", badge: "bg-red-100 text-red-800 border-red-300" },
};

const alertLevelMap: Record<string, { ar: string; badge: string; desc: string }> = {
  NORMAL: {
    ar: "أداء اعتيادي ومقبول",
    badge: "bg-emerald-100 text-emerald-800 border-emerald-300",
    desc: "الانحراف أقل من 15% مقارنة بالتوقعات المعتمدة.",
  },
  WATCH: {
    ar: "تنبيه مراقبة وتحفظ",
    badge: "bg-amber-100 text-amber-800 border-amber-300",
    desc: "انحراف بين 15% و 25% يتطلب مراجعة النفقات والإيرادات.",
  },
  MATERIAL_VARIANCE: {
    ar: "انحراف مالي جوهري",
    badge: "bg-red-100 text-red-800 border-red-300 animate-pulse",
    desc: "انحراف يتجاوز 25% يستدعي إعادة التنبؤ المالي وتحديث خطة السيولة فوراً.",
  },
};

export default function LaunchTab({
  studyId,
  token,
  locale = "ar",
}: {
  studyId: number;
  token: string;
  locale?: "ar" | "en";
}) {
  const ar = locale === "ar";
  const [workspaceData, setWorkspaceData] = useState<LaunchWorkspaceData | null>(null);
  const [subTab, setSubTab] = useState<"milestones" | "actuals" | "variances" | "reforecast">("milestones");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Milestone Form State
  const [newMilestoneCategory, setNewMilestoneCategory] = useState("CR_AND_LICENSING");
  const [newMilestoneTitle, setNewMilestoneTitle] = useState("");
  const [newMilestoneBudget, setNewMilestoneBudget] = useState("5000");
  const [newMilestoneDesc, setNewMilestoneDesc] = useState("");

  // Actuals Form State
  const [actualPeriodNum, setActualPeriodNum] = useState("1");
  const [actualPeriodLabel, setActualPeriodLabel] = useState("M01");
  const [actualRevenue, setActualRevenue] = useState("45000");
  const [actualVolume, setActualVolume] = useState("120");
  const [actualCapex, setActualCapex] = useState("0");
  const [actualSalaries, setActualSalaries] = useState("12000");
  const [actualRent, setActualRent] = useState("6000");
  const [actualInventory, setActualInventory] = useState("5000");
  const [actualMarketing, setActualMarketing] = useState("3000");
  const [actualUtilities, setActualUtilities] = useState("1500");
  const [actualNotes, setActualNotes] = useState("");

  // Reforecast Form State
  const [reforecastReason, setReforecastReason] = useState("");
  const [reforecastBasePeriod, setReforecastBasePeriod] = useState("1");
  const [reforecastRevAdj, setReforecastRevAdj] = useState("-0.10");
  const [reforecastCostAdj, setReforecastCostAdj] = useState("0.05");
  const [reforecastCashBalance, setReforecastCashBalance] = useState("300000");

  const [savingAction, setSavingAction] = useState(false);

  const fetchWorkspace = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getLaunchWorkspace(token, studyId);
      setWorkspaceData(data);
      if (data.actual_periods && data.actual_periods.length > 0) {
        const nextPeriod = data.actual_periods.length + 1;
        setActualPeriodNum(String(nextPeriod));
        setActualPeriodLabel(`M${String(nextPeriod).padStart(2, "0")}`);
      }
    } catch (err: any) {
      setError(err?.message || "فشل تحميل مساحة الإطلاق والأداء الفعلي.");
    } finally {
      setLoading(false);
    }
  }, [token, studyId]);

  useEffect(() => {
    fetchWorkspace();
  }, [fetchWorkspace]);

  const handleAddMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceData) return;
    try {
      setSavingAction(true);
      setError(null);
      await addLaunchMilestone(token, workspaceData.workspace.id, {
        category: newMilestoneCategory,
        title: newMilestoneTitle,
        description: newMilestoneDesc || undefined,
        budget_allocated: parseFloat(newMilestoneBudget) || 0,
      });
      setNewMilestoneTitle("");
      setNewMilestoneDesc("");
      setActionSuccess(ar ? "تمت إضافة المعلم بنجاح" : "Milestone added successfully");
      await fetchWorkspace();
    } catch (err: any) {
      setError(err?.message || "تعذر حفظ المعلم.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleUpdateMilestone = async (milestoneId: number, status: string, cost?: number) => {
    try {
      setSavingAction(true);
      setError(null);
      await updateLaunchMilestone(token, milestoneId, {
        status,
        actual_cost: cost !== undefined ? cost : undefined,
      });
      setActionSuccess(ar ? "تم تحديث حالة المعلم بنجاح" : "Milestone updated");
      await fetchWorkspace();
    } catch (err: any) {
      setError(err?.message || "فشل تحديث المعلم.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleRecordActuals = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceData) return;
    try {
      setSavingAction(true);
      setError(null);

      const opexBreakdown: Record<string, number> = {
        salaries: parseFloat(actualSalaries) || 0,
        rent: parseFloat(actualRent) || 0,
        inventory: parseFloat(actualInventory) || 0,
        marketing: parseFloat(actualMarketing) || 0,
        utilities_gov: parseFloat(actualUtilities) || 0,
      };

      const totalOpex = Object.values(opexBreakdown).reduce((a, b) => a + b, 0);

      await recordLaunchActuals(token, workspaceData.workspace.id, {
        period_number: parseInt(actualPeriodNum, 10) || 1,
        period_label: actualPeriodLabel,
        actual_revenue: parseFloat(actualRevenue) || 0,
        actual_volume: actualVolume ? parseFloat(actualVolume) : undefined,
        actual_capex: parseFloat(actualCapex) || 0,
        actual_opex: totalOpex,
        opex_breakdown: opexBreakdown,
        variance_notes: actualNotes || undefined,
      });

      setActionSuccess(ar ? "تم تسجيل بيانات الفترة الفعلية وحساب الفروقات آلياً" : "Actual period recorded");
      await fetchWorkspace();
      setSubTab("variances");
    } catch (err: any) {
      setError(err?.message || "تعذر تسجيل الأداء الفعلي.");
    } finally {
      setSavingAction(false);
    }
  };

  const handleCreateReforecast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceData) return;
    try {
      setSavingAction(true);
      setError(null);
      await createLaunchReforecast(token, workspaceData.workspace.id, {
        trigger_reason: reforecastReason || (ar ? "تحديث التوقعات بناء على الأداء الفعلي" : "Operational variance update"),
        base_period_number: parseInt(reforecastBasePeriod, 10) || 1,
        revenue_growth_rate_adj: parseFloat(reforecastRevAdj) || 0,
        cost_inflation_adj: parseFloat(reforecastCostAdj) || 0,
        remaining_cash_balance: parseFloat(reforecastCashBalance) || 0,
      });
      setActionSuccess(ar ? "تم توليد سيناريو إعادة التنبؤ وحساب مدرج السيولة النقدية" : "Reforecast scenario generated");
      await fetchWorkspace();
    } catch (err: any) {
      setError(err?.message || "تعذر إنشاء سيناريو إعادة التنبؤ.");
    } finally {
      setSavingAction(false);
    }
  };

  if (loading && !workspaceData) {
    return (
      <div className="p-8 text-center" dir={ar ? "rtl" : "ltr"}>
        <div className="inline-block w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-sm text-slate-600 font-medium">
          {ar ? "جارٍ تحميل نظام الإطلاق وتتبع الأداء الفعلي..." : "Loading Launch & Actuals OS..."}
        </p>
      </div>
    );
  }

  const gate = workspaceData?.decision_gate;
  const milestones = workspaceData?.milestones || [];
  const actualPeriods = workspaceData?.actual_periods || [];
  const varianceSummary = workspaceData?.variance_summary;
  const activeBaseline = workspaceData?.active_baseline;
  const latestReforecast = workspaceData?.latest_reforecast;

  const totalAllocatedBudget = milestones.reduce((s, m) => s + (m.budget_allocated || 0), 0);
  const totalActualMilestoneCost = milestones.reduce((s, m) => s + (m.actual_cost || 0), 0);
  const completedMilestonesCount = milestones.filter((m) => m.status === "COMPLETED").length;

  return (
    <div className="space-y-6" dir={ar ? "rtl" : "ltr"}>
      {/* HEADER */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200">
                {ar ? "الموجة 5: نظام الإطلاق والتنفيذ الفعلي" : "Wave 5: Launch & Actuals OS"}
              </span>
              <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-700">
                Baseline {activeBaseline?.version || "v1"}
              </span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">
              {ar ? "تنفيذ الإطلاق والربط الفعلي والتنبؤ التكيفي" : "Launch Execution, Actuals & Reforecasting"}
            </h2>
            <p className="text-sm text-slate-600 mt-1">
              {ar
                ? "إدارة متطلبات الإطلاق السعودي، مقارنة الأداء الفعلي مع دراسة الجدوى بدون تزييف، ومراقبة مدرج السيولة النقدية."
                : "Manage Saudi launch milestones, track real operational actuals against frozen baseline, and calculate dynamic cash runway."}
            </p>
          </div>

          {/* DECISION GATE BADGE */}
          {gate && (
            <div
              className={`p-3 rounded-lg border text-sm font-medium ${
                gate.is_allowed
                  ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                  : "bg-red-50 border-red-200 text-red-900"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-base">{gate.is_allowed ? "🔓" : "🔒"}</span>
                <span className="font-bold">
                  {gate.is_allowed
                    ? ar
                      ? `بوابة الإطلاق مفتوحة (${gate.decision})`
                      : `Launch Gate Unlocked (${gate.decision})`
                    : ar
                    ? "بوابة الإطلاق مقفلة بقرار التحقق"
                    : "Launch Gate Locked by Validation"}
                </span>
              </div>
              <p className="text-xs mt-1 text-slate-600 max-w-sm">{gate.reason}</p>
            </div>
          )}
        </div>

        {/* FEEDBACK ALERTS */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-xs underline font-semibold">
              {ar ? "إغلاق" : "Dismiss"}
            </button>
          </div>
        )}

        {actionSuccess && (
          <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg flex items-center justify-between">
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} className="text-xs underline font-semibold">
              {ar ? "إغلاق" : "Dismiss"}
            </button>
          </div>
        )}

        {/* GATE RESTRICTION BANNER */}
        {gate && !gate.is_allowed && (
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 text-sm">
            <h4 className="font-bold text-base mb-1">
              ⚠️ {ar ? "تنبيه الحوكمة المالية والتشغيلية" : "Operational Governance Alert"}
            </h4>
            <p>
              {ar
                ? "وفقاً لمحددات الحوكمة، لا يمكن بدء عمليات الإطلاق الفعلي أو تسجيل المصاريف التشغيلية للمشاريع التي صدر لها قرار إيقاف (STOP) أو تتطلب تعديل مسار (PIVOT). يرجى مراجعة تبويب \"التحقق الميداني\" لتسجيل الأدلة وتحديث القرار إلى GO أو GO_WITH_CONDITIONS."
                : "Projects with a STOP or PIVOT validation decision are blocked from launching. Please review Market Validation tab to document evidence and resolve gate requirements."}
            </p>
          </div>
        )}

        {/* NAVIGATION TABS */}
        <div className="flex border-b border-slate-200 mt-6 gap-2">
          <button
            onClick={() => setSubTab("milestones")}
            className={`pb-3 px-4 text-sm font-semibold border-b-2 transition ${
              subTab === "milestones"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {ar ? `معالم الإطلاق والتشغيل (${milestones.length})` : `Launch Milestones (${milestones.length})`}
          </button>
          <button
            onClick={() => setSubTab("actuals")}
            className={`pb-3 px-4 text-sm font-semibold border-b-2 transition ${
              subTab === "actuals"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {ar ? `تسجيل الأداء الفعلي (${actualPeriods.length})` : `Record Actuals (${actualPeriods.length})`}
          </button>
          <button
            onClick={() => setSubTab("variances")}
            className={`pb-3 px-4 text-sm font-semibold border-b-2 transition ${
              subTab === "variances"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {ar ? "مقارنة التوقعات مع الفعلي (Variance)" : "Forecast vs Actual Matrix"}
          </button>
          <button
            onClick={() => setSubTab("reforecast")}
            className={`pb-3 px-4 text-sm font-semibold border-b-2 transition ${
              subTab === "reforecast"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {ar ? "إعادة التنبؤ ومدرج السيولة" : "Reforecast & Runway"}
          </button>
        </div>
      </div>

      {/* SUBTAB 1: MILESTONES */}
      {subTab === "milestones" && (
        <div className="space-y-6">
          {/* STATS OVERVIEW */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">{ar ? "إجمالي المعالم" : "Total Milestones"}</span>
              <p className="text-2xl font-bold text-slate-800 mt-1">{milestones.length}</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">{ar ? "المعالم المكتملة" : "Completed"}</span>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                {completedMilestonesCount} / {milestones.length}
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">{ar ? "الميزانية المخصصة" : "Allocated Budget"}</span>
              <p className="text-2xl font-bold text-indigo-700 mt-1">
                {totalAllocatedBudget.toLocaleString()} <span className="text-xs font-normal text-slate-500">ر.س</span>
              </p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-xs text-slate-500 font-medium">{ar ? "المصروف الفعلي" : "Actual Cost"}</span>
              <p className="text-2xl font-bold text-slate-900 mt-1">
                {totalActualMilestoneCost.toLocaleString()} <span className="text-xs font-normal text-slate-500">ر.س</span>
              </p>
            </div>
          </div>

          {/* MILESTONES LIST */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm">
                {ar ? "خطة المعالم والاشتراطات التشغيلية السعودية" : "Saudi Regulatory & Operational Milestones"}
              </h3>
              <span className="text-xs text-slate-500">
                {ar ? "التحديث الفوري لتكاليف التأسيس" : "Real-time Setup Cost Tracking"}
              </span>
            </div>

            <div className="divide-y divide-slate-100">
              {milestones.map((m) => {
                const catObj = milestoneCategories.find((c) => c.value === m.category);
                const statusMeta = milestoneStatusMap[m.status] || milestoneStatusMap.PENDING;
                return (
                  <div key={m.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${statusMeta.badge}`}>
                          {statusMeta.ar}
                        </span>
                        <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                          {catObj ? catObj.ar : m.category}
                        </span>
                      </div>
                      <h4 className="font-bold text-slate-800 text-sm">{m.title}</h4>
                      {m.description && <p className="text-xs text-slate-600 max-w-xl">{m.description}</p>}
                    </div>

                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="text-xs text-slate-500">{ar ? "المخصص / الفعلي" : "Budget / Actual"}</div>
                        <div className="text-sm font-semibold text-slate-800">
                          {m.budget_allocated.toLocaleString()} /{" "}
                          <span className={m.actual_cost > m.budget_allocated ? "text-red-600" : "text-emerald-600"}>
                            {m.actual_cost.toLocaleString()}
                          </span>{" "}
                          <span className="text-xs font-normal text-slate-500">ر.س</span>
                        </div>
                      </div>

                      {/* QUICK ACTIONS */}
                      <div className="flex items-center gap-1">
                        {m.status !== "COMPLETED" && (
                          <button
                            disabled={savingAction}
                            onClick={() => handleUpdateMilestone(m.id, "COMPLETED", m.actual_cost || m.budget_allocated)}
                            className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded hover:bg-emerald-100 transition"
                          >
                            ✓ {ar ? "إكمال" : "Complete"}
                          </button>
                        )}
                        {m.status !== "IN_PROGRESS" && m.status !== "COMPLETED" && (
                          <button
                            disabled={savingAction}
                            onClick={() => handleUpdateMilestone(m.id, "IN_PROGRESS")}
                            className="px-2.5 py-1 text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 rounded hover:bg-blue-100 transition"
                          >
                            ▶ {ar ? "بدء" : "Start"}
                          </button>
                        )}
                        {m.status !== "BLOCKED" && (
                          <button
                            disabled={savingAction}
                            onClick={() => handleUpdateMilestone(m.id, "BLOCKED")}
                            className="px-2.5 py-1 text-xs font-semibold bg-red-50 text-red-700 border border-red-200 rounded hover:bg-red-100 transition"
                          >
                            ✕ {ar ? "تعثر" : "Block"}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ADD MILESTONE FORM */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-slate-900 text-sm mb-4">
              {ar ? "إضافة معلم أو اشتراط تشغيلي جديد" : "Add Custom Launch Milestone"}
            </h3>
            <form onSubmit={handleAddMilestone} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "التصنيف التشغيلي" : "Operational Category"}
                  </label>
                  <select
                    value={newMilestoneCategory}
                    onChange={(e) => setNewMilestoneCategory(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white"
                  >
                    {milestoneCategories.map((c) => (
                      <option key={c.value} value={c.value}>
                        {c.ar}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "عنوان المعلم / الإجراء" : "Milestone Title"}
                  </label>
                  <input
                    type="text"
                    required
                    value={newMilestoneTitle}
                    onChange={(e) => setNewMilestoneTitle(e.target.value)}
                    placeholder={ar ? "مثال: إصدار ترخيص بلدي تجاري" : "e.g. Municipal commercial license"}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "الميزانية المخصصة (ر.س)" : "Allocated Budget (SAR)"}
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={newMilestoneBudget}
                    onChange={(e) => setNewMilestoneBudget(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  {ar ? "التفاصيل والمتطلبات التنظيمية" : "Requirements & Description"}
                </label>
                <textarea
                  rows={2}
                  value={newMilestoneDesc}
                  onChange={(e) => setNewMilestoneDesc(e.target.value)}
                  placeholder={ar ? "متطلبات الجهة الحكومية أو المورد..." : "Requirements details..."}
                  className="w-full text-sm border border-slate-300 rounded-lg p-2"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={savingAction || !newMilestoneTitle}
                  className="px-4 py-2 text-sm font-bold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition"
                >
                  {savingAction ? (ar ? "جارٍ الإضافة..." : "Adding...") : ar ? "+ حفظ المعلم" : "+ Add Milestone"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SUBTAB 2: RECORD ACTUALS */}
      {subTab === "actuals" && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-bold text-slate-900 text-base">
                  {ar ? "تسجيل بيانات الشهر الفعلي (Actuals Entry)" : "Record Monthly Actuals"}
                </h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  {ar
                    ? "أدخل الإيرادات والمصاريف التشغيلية الفعلية بدقة. لا يتم استخدام أي بيانات وهمية أو تقديرات مصطنعة."
                    : "Enter real revenue and OPEX breakdown without fabricated data."}
                </p>
              </div>
              <span className="text-xs px-2.5 py-1 bg-indigo-50 text-indigo-700 font-semibold rounded-full border border-indigo-100">
                {ar ? "تفصيل المصروفات التشغيلية (OPEX)" : "OPEX Categorization"}
              </span>
            </div>

            <form onSubmit={handleRecordActuals} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "رقم الفترة (الشهر)" : "Period Number"}
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={actualPeriodNum}
                    onChange={(e) => {
                      setActualPeriodNum(e.target.value);
                      setActualPeriodLabel(`M${String(e.target.value).padStart(2, "0")}`);
                    }}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "تسمية الفترة" : "Period Label"}
                  </label>
                  <input
                    type="text"
                    required
                    value={actualPeriodLabel}
                    onChange={(e) => setActualPeriodLabel(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-slate-50"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "الإيراد الفعلي المحقق (ر.س)" : "Actual Revenue (SAR)"}
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    required
                    value={actualRevenue}
                    onChange={(e) => setActualRevenue(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2 font-semibold text-emerald-700"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "حجم المبيعات / عدد العمليات" : "Actual Volume / Transactions"}
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={actualVolume}
                    onChange={(e) => setActualVolume(e.target.value)}
                    placeholder="e.g. 120"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              {/* OPEX BREAKDOWN GRID */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <h4 className="font-bold text-slate-800 text-xs mb-3">
                  {ar ? "توزيع المصاريف التشغيلية الفعلية (ر.س):" : "Actual OPEX Breakdown (SAR):"}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-1">{ar ? "الرواتب والتوطين" : "Salaries & Saudization"}</label>
                    <input
                      type="number"
                      min="0"
                      value={actualSalaries}
                      onChange={(e) => setActualSalaries(e.target.value)}
                      className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-1">{ar ? "الإيجار والموقع" : "Rent & Facility"}</label>
                    <input
                      type="number"
                      min="0"
                      value={actualRent}
                      onChange={(e) => setActualRent(e.target.value)}
                      className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-1">{ar ? "المخزون والبضاعة" : "Inventory & Goods"}</label>
                    <input
                      type="number"
                      min="0"
                      value={actualInventory}
                      onChange={(e) => setActualInventory(e.target.value)}
                      className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-1">{ar ? "التسويق والإعلانات" : "Marketing & Ads"}</label>
                    <input
                      type="number"
                      min="0"
                      value={actualMarketing}
                      onChange={(e) => setActualMarketing(e.target.value)}
                      className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-600 mb-1">{ar ? "المرافق والرسوم" : "Utilities & Gov Fees"}</label>
                    <input
                      type="number"
                      min="0"
                      value={actualUtilities}
                      onChange={(e) => setActualUtilities(e.target.value)}
                      className="w-full text-sm border border-slate-300 rounded-lg p-2 bg-white"
                    />
                  </div>
                </div>

                <div className="mt-3 text-left font-bold text-xs text-slate-700">
                  {ar ? "إجمالي المصاريف التشغيلية (OPEX): " : "Total OPEX: "}
                  <span className="text-sm text-indigo-700">
                    {(
                      (parseFloat(actualSalaries) || 0) +
                      (parseFloat(actualRent) || 0) +
                      (parseFloat(actualInventory) || 0) +
                      (parseFloat(actualMarketing) || 0) +
                      (parseFloat(actualUtilities) || 0)
                    ).toLocaleString()}{" "}
                    ر.س
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "المصاريف الرأسمالية الإضافية (CAPEX إن وجدت)" : "Actual Additional CAPEX (if any)"}
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={actualCapex}
                    onChange={(e) => setActualCapex(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "ملاحظات وأسباب الفروقات في هذا الشهر" : "Variance Reasons & Notes"}
                  </label>
                  <input
                    type="text"
                    value={actualNotes}
                    onChange={(e) => setActualNotes(e.target.value)}
                    placeholder={ar ? "مثال: تأخر استلام بضاعة أو حملة تسويقية ناجحة..." : "Operational context..."}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={savingAction}
                  className="px-5 py-2 text-sm font-bold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition"
                >
                  {savingAction ? (ar ? "جارٍ الحفظ..." : "Recording...") : ar ? "✓ تسجيل بيانات الفترة وحساب الفروقات" : "✓ Record Period"}
                </button>
              </div>
            </form>
          </div>

          {/* RECORDED PERIODS HISTORY */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm">
                {ar ? "سجل الأشهر الفعلية المسجلة" : "Historical Recorded Periods"}
              </h3>
              <span className="text-xs font-semibold text-slate-600">
                {actualPeriods.length} {ar ? "فترات مسجلة" : "periods"}
              </span>
            </div>

            {actualPeriods.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                {ar ? "لم يتم تسجيل أي فترات تشغيلية بعد. استخدم النموذج أعلاه لتسجيل الشهر الأول." : "No actual periods recorded yet."}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-right text-xs">
                  <thead className="bg-slate-100 text-slate-700 font-semibold border-b">
                    <tr>
                      <th className="p-3">الفترة</th>
                      <th className="p-3">الإيراد الفعلي</th>
                      <th className="p-3">المصاريف التشغيلية (OPEX)</th>
                      <th className="p-3">المصاريف الرأسمالية (CAPEX)</th>
                      <th className="p-3">صافي التدفق النقدي</th>
                      <th className="p-3">الملاحظات</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {actualPeriods.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50">
                        <td className="p-3 font-bold text-slate-800">{p.period_label}</td>
                        <td className="p-3 font-semibold text-emerald-700">{p.actual_revenue.toLocaleString()} ر.س</td>
                        <td className="p-3 text-slate-700">{p.actual_opex.toLocaleString()} ر.س</td>
                        <td className="p-3 text-slate-700">{p.actual_capex.toLocaleString()} ر.س</td>
                        <td className={`p-3 font-bold ${p.net_cashflow >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                          {p.net_cashflow.toLocaleString()} ر.س
                        </td>
                        <td className="p-3 text-slate-500 max-w-xs truncate">{p.variance_notes || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUBTAB 3: FORECAST VS ACTUAL VARIANCE MATRIX */}
      {subTab === "variances" && (
        <div className="space-y-6">
          {varianceSummary && (
            <>
              {/* CUMULATIVE SUMMARY CARDS */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs text-slate-500 font-medium">{ar ? "الإيراد المتوقع التراكمي" : "Cumulative Forecast Rev"}</span>
                  <p className="text-xl font-bold text-slate-800 mt-1">
                    {varianceSummary.cumulative_forecast_revenue.toLocaleString()} <span className="text-xs font-normal">ر.س</span>
                  </p>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs text-slate-500 font-medium">{ar ? "الإيراد الفعلي التراكمي" : "Cumulative Actual Rev"}</span>
                  <p className="text-xl font-bold text-emerald-700 mt-1">
                    {varianceSummary.cumulative_actual_revenue.toLocaleString()} <span className="text-xs font-normal">ر.س</span>
                  </p>
                  <div className="text-xs font-semibold mt-1">
                    {varianceSummary.cumulative_revenue_variance >= 0 ? "+" : ""}
                    {varianceSummary.cumulative_revenue_variance.toLocaleString()} ر.س (
                    {varianceSummary.cumulative_revenue_variance_pct !== null ? `${varianceSummary.cumulative_revenue_variance_pct}%` : "—"})
                  </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs text-slate-500 font-medium">{ar ? "المصاريف التشغيلية التراكمية" : "Cumulative OPEX"}</span>
                  <p className="text-xl font-bold text-indigo-700 mt-1">
                    {varianceSummary.cumulative_actual_opex.toLocaleString()} <span className="text-xs font-normal">ر.س</span>
                  </p>
                  <div className="text-xs text-slate-500 mt-1">
                    {ar ? "المتوقع: " : "Forecast: "}
                    {varianceSummary.cumulative_forecast_opex.toLocaleString()} ر.س
                  </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-xs text-slate-500 font-medium">{ar ? "أعلى مستوى تنبيه" : "Highest Materiality Alert"}</span>
                  <div className="mt-2">
                    {(() => {
                      const alert = alertLevelMap[varianceSummary.highest_alert_level] || alertLevelMap.NORMAL;
                      return (
                        <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${alert.badge}`}>
                          {alert.ar}
                        </span>
                      );
                    })()}
                  </div>
                </div>
              </div>

              {/* DETAILED VARIANCE MATRIX TABLE */}
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 text-sm">
                    {ar ? "مصفوفة تحليل الانحرافات الشهرية (Forecast vs Actual)" : "Monthly Variance Matrix"}
                  </h3>
                  <span className="text-xs text-slate-500">
                    {ar ? "حساب الانحراف النسبي بدون قسمة على الصفر" : "Zero-division protected variance"}
                  </span>
                </div>

                {varianceSummary.periods.length === 0 ? (
                  <div className="p-8 text-center text-slate-500 text-sm">
                    {ar ? "سجل فترات تشغيلية أولاً لمشاهدة تحليل الانحرافات." : "Record actual periods to see variance matrix."}
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-right text-xs">
                      <thead className="bg-slate-100 text-slate-700 font-semibold border-b">
                        <tr>
                          <th className="p-3">الفترة</th>
                          <th className="p-3">الإيراد (توقع / فعلي)</th>
                          <th className="p-3">انحراف الإيراد</th>
                          <th className="p-3">المصاريف (توقع / فعلي)</th>
                          <th className="p-3">انحراف المصاريف</th>
                          <th className="p-3">التدفق النقدي</th>
                          <th className="p-3">مستوى التنبيه</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {varianceSummary.periods.map((item: LaunchVarianceReport) => {
                          const alertMeta = alertLevelMap[item.alert_level] || alertLevelMap.NORMAL;
                          return (
                            <tr key={item.period_number} className="hover:bg-slate-50">
                              <td className="p-3 font-bold text-slate-800">{item.period_label}</td>
                              <td className="p-3">
                                <div>{item.actual_revenue.toLocaleString()} ر.س</div>
                                <div className="text-[11px] text-slate-400">توقع: {item.forecast_revenue.toLocaleString()}</div>
                              </td>
                              <td className="p-3">
                                <span className={`font-semibold ${item.revenue_variance >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                                  {item.revenue_variance >= 0 ? "+" : ""}
                                  {item.revenue_variance.toLocaleString()} ر.س
                                </span>
                                {item.revenue_variance_pct !== null && (
                                  <div className="text-[10px] text-slate-500">{item.revenue_variance_pct}%</div>
                                )}
                              </td>
                              <td className="p-3">
                                <div>{item.actual_opex.toLocaleString()} ر.س</div>
                                <div className="text-[11px] text-slate-400">توقع: {item.forecast_opex.toLocaleString()}</div>
                              </td>
                              <td className="p-3">
                                <span className={`font-semibold ${item.opex_variance <= 0 ? "text-emerald-600" : "text-amber-600"}`}>
                                  {item.opex_variance >= 0 ? "+" : ""}
                                  {item.opex_variance.toLocaleString()} ر.س
                                </span>
                                {item.opex_variance_pct !== null && (
                                  <div className="text-[10px] text-slate-500">{item.opex_variance_pct}%</div>
                                )}
                              </td>
                              <td className={`p-3 font-bold ${item.actual_net_cashflow >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                                {item.actual_net_cashflow.toLocaleString()} ر.س
                              </td>
                              <td className="p-3">
                                <span className={`px-2 py-0.5 text-[11px] font-bold rounded-full border ${alertMeta.badge}`}>
                                  {alertMeta.ar}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* SUBTAB 4: REFORECAST & RUNWAY */}
      {subTab === "reforecast" && (
        <div className="space-y-6">
          {/* RUNWAY HIGHLIGHT BANNER */}
          {latestReforecast && (
            <div className="bg-gradient-to-l from-indigo-50 via-white to-slate-50 border border-indigo-200 rounded-xl p-6 shadow-sm">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-indigo-600 text-white">
                      {latestReforecast.version}
                    </span>
                    <span className="text-xs text-slate-500">
                      {ar ? "سبب التوليد: " : "Trigger: "} {latestReforecast.trigger_reason}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">
                    {ar ? "مؤشرات السيولة ومدرج النجاة المالي (Cash Runway)" : "Cash Runway & Burn Rate Metrics"}
                  </h3>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <span className="text-xs text-slate-500">{ar ? "معدل الحرق الشهري" : "Monthly Burn Rate"}</span>
                    <p className="text-xl font-bold text-red-600">
                      {latestReforecast.monthly_burn_rate.toLocaleString()}{" "}
                      <span className="text-xs font-normal text-slate-500">ر.س/شهر</span>
                    </p>
                  </div>
                  <div className="text-right border-r pr-6 border-slate-200">
                    <span className="text-xs text-slate-500">{ar ? "مدرج السيولة المتبقي" : "Estimated Runway"}</span>
                    <p className="text-2xl font-black text-indigo-700">
                      {latestReforecast.runway_months !== null ? `${latestReforecast.runway_months} شهر` : "تدفق إيجابي"}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TRIGGER REFORECAST FORM */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-slate-900 text-sm mb-1">
              {ar ? "توليد سيناريو إعادة التنبؤ (Trigger Dynamic Reforecast)" : "Generate Dynamic Reforecast"}
            </h3>
            <p className="text-xs text-slate-600 mb-4">
              {ar
                ? "يسمح بتعديل مسار التوقعات للأشهر القادمة بناءً على الأداء الفعلي ومعدل التضخم أو نمو الطلب، واحتساب السيولة النقدية المتبقية."
                : "Adjust forward projections based on actual performance and remaining cash balance."}
            </p>

            <form onSubmit={handleCreateReforecast} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "سبب إعادة التنبؤ" : "Trigger Reason"}
                  </label>
                  <input
                    type="text"
                    required
                    value={reforecastReason}
                    onChange={(e) => setReforecastReason(e.target.value)}
                    placeholder={ar ? "مثال: انحراف الإيرادات في الشهر الأول" : "e.g. Month 1 revenue shortfall"}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "الانطلاق من نهاية الفترة" : "Base Period Number"}
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={reforecastBasePeriod}
                    onChange={(e) => setReforecastBasePeriod(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "الرصيد النقدي الفعلي المتبقي في البنك (ر.س)" : "Remaining Cash Balance (SAR)"}
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    required
                    value={reforecastCashBalance}
                    onChange={(e) => setReforecastCashBalance(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2 font-bold text-slate-900"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "تعديل وتيرة نمو الإيراد (Adjustment %)" : "Revenue Growth Rate Adjustment %"}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={reforecastRevAdj}
                    onChange={(e) => setReforecastRevAdj(e.target.value)}
                    placeholder="-0.10 (-10%) or +0.05 (+5%)"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1">
                    {ar ? "تعديل تضخم التكاليف التشغيلية (Inflation %)" : "Cost Inflation Adjustment %"}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={reforecastCostAdj}
                    onChange={(e) => setReforecastCostAdj(e.target.value)}
                    placeholder="0.05 (+5%)"
                    className="w-full text-sm border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={savingAction || !reforecastReason}
                  className="px-5 py-2 text-sm font-bold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition"
                >
                  {savingAction ? (ar ? "جارٍ الحساب..." : "Generating...") : ar ? "⚡ توليد سيناريو إعادة التنبؤ" : "⚡ Generate Reforecast"}
                </button>
              </div>
            </form>
          </div>

          {/* REFORECAST PROJECTIONS TABLE */}
          {latestReforecast && (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
                <h3 className="font-bold text-slate-900 text-sm">
                  {ar ? `مسار التوقعات المحدثة (${latestReforecast.version})` : `Updated Projection Trajectory (${latestReforecast.version})`}
                </h3>
                <span className="text-xs text-slate-500 font-medium">12 {ar ? "شهر قادم" : "Months Forward"}</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-right text-xs">
                  <thead className="bg-slate-100 text-slate-700 font-semibold border-b">
                    <tr>
                      <th className="p-3">الفترة</th>
                      <th className="p-3">الإيراد المتوقع المحدث</th>
                      <th className="p-3">المصاريف المتوقعة</th>
                      <th className="p-3">صافي التدفق</th>
                      <th className="p-3">الرصيد النقدي التقديري</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {latestReforecast.scenario_projections.map((sp: any) => (
                      <tr key={sp.month} className="hover:bg-slate-50">
                        <td className="p-3 font-bold text-slate-800">{sp.period_label}</td>
                        <td className="p-3 font-semibold text-emerald-700">{sp.projected_revenue.toLocaleString()} ر.س</td>
                        <td className="p-3 text-slate-700">{sp.projected_opex.toLocaleString()} ر.س</td>
                        <td className={`p-3 font-bold ${sp.projected_net_cashflow >= 0 ? "text-emerald-700" : "text-red-600"}`}>
                          {sp.projected_net_cashflow.toLocaleString()} ر.س
                        </td>
                        <td className={`p-3 font-bold ${sp.projected_cash_balance >= 0 ? "text-slate-800" : "text-red-600"}`}>
                          {sp.projected_cash_balance.toLocaleString()} ر.س
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
