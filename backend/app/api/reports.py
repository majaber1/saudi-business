"""
Report generation & download API.

  GET /reports/study/{study_id}?fmt=pdf|docx&locale=ar|en
      -> streams a freshly generated bilingual feasibility report and records
         a Report row for audit/history.

Requires persistence. In demo mode returns 503 (no study to report on).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, get_current_user
from app.services.reporting import build_report_context, generate_pdf, generate_docx

router = APIRouter(prefix="/reports", tags=["reports"])


def _require_db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Reports require persistence (database not configured).")
    return SessionLocal()


def _latest_result(db, models, study_id: int):
    row = (
        db.query(models.FinancialResult)
        .filter_by(study_id=study_id)
        .order_by(models.FinancialResult.id.desc())
        .first()
    )
    if row is None:
        return None
    detail = row.detail or {}
    return {
        "roi_percent": row.roi,
        "payback_years": row.payback_years,
        "npv": row.npv,
        "irr_percent": (row.irr * 100) if row.irr is not None else None,
        "verdict": row.verdict,
        "sensitivity": detail.get("sensitivity", []),
    }


@router.get("/study/{study_id}")
def download_report(
    study_id: int,
    fmt: str = Query("pdf", pattern="^(pdf|docx)$"),
    locale: str = Query("ar", pattern="^(ar|en)$"),
    user: UserOut = Depends(get_current_user),
):
    from app import models

    db = _require_db()
    try:
        study = db.get(models.FeasibilityStudy, study_id)
        if study is None:
            raise HTTPException(status_code=404, detail="Study not found")
        project = db.get(models.Project, study.project_id)
        result = _latest_result(db, models, study.id)
        ctx = build_report_context(study, result, project)

        if fmt == "pdf":
            data = generate_pdf(ctx, locale)
            media = "application/pdf"
            ext = "pdf"
        else:
            data = generate_docx(ctx, locale)
            media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ext = "docx"

        db.add(models.Report(study_id=study.id, fmt=ext, locale=locale, version="1.0"))
        db.add(models.AuditLog(actor_id=user.id, action="report.generate", entity="study",
                               entity_id=study.id, meta={"fmt": ext, "locale": locale}))
        db.commit()

        filename = "feasibility_%d_%s.%s" % (study.id, locale, ext)
        headers = {"Content-Disposition": "attachment; filename=" + filename}
        return Response(content=data, media_type=media, headers=headers)
    finally:
        db.close()
