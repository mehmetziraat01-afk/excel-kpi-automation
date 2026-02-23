"""Suspicious production batch UI/API routes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Header, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from yem_sistem.db.session import get_session
from yem_sistem.production_batches.service import (
    BatchFixAuthorizationError,
    BatchFixValidationError,
    ProductionBatchService,
)

router = APIRouter(tags=["batches"])


def _require_admin(x_role: str) -> None:
    if (x_role or "").upper() != "ADMIN":
        raise HTTPException(status_code=403, detail="Only ADMIN can access this endpoint")


@router.get("/batches/suspicious", response_class=HTMLResponse)
def suspicious_batches_page(
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> str:
    _require_admin(x_role)
    service = ProductionBatchService(session)
    batches = service.list_suspicious_batches(limit=100)

    rows = "".join(
        f"<tr><td>{b.id}</td><td>{b.id_batch}</td><td>{b.batch_name}</td><td>{b.date}</td><td>{b.suspicious_count_zero}</td>"
        f"<td>{b.suspicious_reason or ''}</td><td><a class='btn btn-sm btn-primary' href='/batches/{b.id}/fix'>Fix</a></td></tr>"
        for b in batches
    )

    return f"""
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Suspicious Batches</title>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
</head>
<body class='bg-light'>
<div class='container py-4'>
  <h1 class='mb-3'>Suspicious Batches</h1>
  <div class='table-responsive card shadow-sm'>
    <table class='table table-striped mb-0'>
      <thead><tr><th>ID</th><th>ID Batch</th><th>Batch</th><th>Date</th><th>Zero Count</th><th>Reason</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>
</body>
</html>
"""


@router.get("/batches/{batch_id}/fix", response_class=HTMLResponse)
def fix_batch_page(
    batch_id: int,
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> str:
    _require_admin(x_role)
    service = ProductionBatchService(session)
    try:
        batch, items = service.get_zero_loaded_items(batch_id)
    except BatchFixValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    item_rows = "".join(
        f"<tr><td>{i.id}</td><td>{i.material_id}</td><td>{i.target_weight}</td><td>{i.loaded_weight}</td><td>{i.corrected_weight or ''}</td><td>{i.correction_note or ''}</td></tr>"
        for i in items
    )

    return f"""
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Fix Batch #{batch.id}</title>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
</head>
<body class='bg-light'>
<div class='container py-4'>
  <h1 class='mb-1'>Fix Batch #{batch.id} ({batch.id_batch})</h1>
  <p class='text-muted'>Only zero-loaded items are shown.</p>

  <div class='card shadow-sm mb-4'>
    <div class='card-body'>
      <form method='post' action='/batches/{batch.id}/fix-item'>
        <div class='row g-3'>
          <div class='col-md-3'><label class='form-label'>Batch Item ID</label><input name='batch_item_id' type='number' class='form-control' required></div>
          <div class='col-md-3'><label class='form-label'>Corrected Weight</label><input name='corrected_weight' type='number' step='0.001' class='form-control' required></div>
          <div class='col-md-6'><label class='form-label'>Correction Note (min 15)</label><input name='correction_note' class='form-control' required></div>
        </div>
        <button type='submit' class='btn btn-primary mt-3'>Fix Item</button>
      </form>
    </div>
  </div>

  <div class='table-responsive card shadow-sm'>
    <table class='table table-striped mb-0'>
      <thead><tr><th>Item ID</th><th>Material ID</th><th>Target</th><th>Loaded</th><th>Corrected</th><th>Note</th></tr></thead>
      <tbody>{item_rows}</tbody>
    </table>
  </div>
</div>
</body>
</html>
"""


@router.post("/batches/{batch_id}/fix-item")
def fix_batch_item(
    batch_id: int,
    batch_item_id: int = Form(...),
    corrected_weight: str = Form(...),
    correction_note: str = Form(...),
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> dict:
    service = ProductionBatchService(session)
    try:
        item = service.fix_item(
            batch_id=batch_id,
            batch_item_id=batch_item_id,
            corrected_weight=Decimal(corrected_weight),
            correction_note=correction_note,
            actor_role=x_role,
        )
        return {"status": "fixed", "batch_item_id": item.id}
    except BatchFixAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except BatchFixValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
