import Link from "next/link";

export default function NotFound() {
  return (
    <section className="container-page grid min-h-[60vh] place-items-center py-16 text-center">
      <div>
        <p className="text-sm font-bold tracking-[0.2em] text-gold-700">404</p>
        <h1 className="mt-3 text-3xl font-bold text-ink-900">Page not found · الصفحة غير موجودة</h1>
        <p className="mt-3 text-ink-600">Return to your business workspace · ارجع إلى مساحة أعمالك</p>
        <Link href="/dashboard" className="mt-6 inline-flex rounded-xl bg-brand-600 px-5 py-3 text-sm font-bold text-white hover:bg-brand-700">Dashboard · لوحة التحكم</Link>
      </div>
    </section>
  );
}
