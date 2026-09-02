"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { createStudy, getProject, getToken, listStudies, type Project, type Study } from "@/lib/api";
import { useLanguage } from "@/components/LanguageProvider";

export default function ProjectWorkspacePage({ params }: { params: Promise<{ projectId: string }> }) {
  const { projectId: rawProjectId } = use(params);
  const projectId = Number(rawProjectId);
  const { locale } = useLanguage();
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [study, setStudy] = useState<Study | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const token = getToken();

  useEffect(() => {
    if (!token || !Number.isInteger(projectId)) { setLoading(false); return; }
    Promise.all([getProject(token, projectId), listStudies(token, projectId)])
      .then(([projectRow, studies]) => { setProject(projectRow); setStudy(studies[0] ?? null); })
      .catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)))
      .finally(() => setLoading(false));
  }, [projectId, token]);

  async function startStudy() {
    if (!token || !project || creating) return;
    setCreating(true); setError("");
    try {
      const existing = (await listStudies(token, project.id))[0];
      const target = existing ?? await createStudy(token, { title: project.name, industry: project.industry, investment: project.investment, project_id: project.id, study_type: "business_decision" });
      router.push(`/projects/${project.id}/studies/${target.id}`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); setCreating(false); }
  }

  if (!token) return <main className="container-page py-16"><p>{locale === "ar" ? "سجّل الدخول لفتح هذا المشروع." : "Sign in to open this project."}</p><Link className="mt-4 inline-flex rounded-lg bg-brand-600 px-4 py-2 text-white" href={`/login?next=${encodeURIComponent(`/projects/${projectId}`)}`}>{locale === "ar" ? "تسجيل الدخول" : "Sign in"}</Link></main>;
  if (loading) return <main className="container-page py-16">{locale === "ar" ? "جارٍ تحميل المشروع..." : "Loading project..."}</main>;
  if (error || !project) return <main className="container-page py-16"><p role="alert" className="rounded-lg bg-red-50 p-4 text-red-700">{error || (locale === "ar" ? "تعذر العثور على المشروع." : "Project not found.")}</p></main>;

  return <main className="container-page py-12"><Link href="/projects" className="text-sm text-brand-700">{locale === "ar" ? "العودة إلى المشاريع" : "Back to projects"}</Link><section className="mt-5 rounded-2xl border border-slate-200 bg-white p-7 shadow-sm"><p className="text-sm text-ink-500">{locale === "ar" ? "مساحة المشروع" : "Project workspace"}</p><h1 className="mt-1 text-3xl font-bold">{project.name}</h1><p className="mt-3 text-ink-600">{new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-SA", { style: "currency", currency: "SAR", maximumFractionDigits: 0 }).format(project.investment)}</p><div className="mt-7">{study ? <Link href={`/projects/${project.id}/studies/${study.id}`} className="inline-flex rounded-lg bg-brand-600 px-5 py-3 font-medium text-white">{study.status === "completed" ? (locale === "ar" ? "عرض القرار" : "View decision") : (locale === "ar" ? "متابعة الدراسة" : "Continue study")}</Link> : <button onClick={() => void startStudy()} disabled={creating} className="rounded-lg bg-brand-600 px-5 py-3 font-medium text-white disabled:opacity-60">{creating ? (locale === "ar" ? "جارٍ الإنشاء..." : "Creating...") : (locale === "ar" ? "ابدأ الدراسة" : "Start study")}</button>}</div></section></main>;
}
