"""Acceptance HTTP routes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Header, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from yem_sistem.acceptance.service import (
    AcceptanceAuthorizationError,
    AcceptanceCreateInput,
    AcceptanceService,
    AcceptanceValidationError,
    parse_datetime,
)
from yem_sistem.db.session import get_session

router = APIRouter(tags=["acceptance"])


@router.post("/acceptance")
def create_acceptance(
    date: str = Form(...),
    plate: str = Form(...),
    material_id: int = Form(...),
    quantity: str = Form(...),
    company: str | None = Form(default=None),
    note: str | None = Form(default=None),
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> dict:
    service = AcceptanceService(session)
    try:
        acceptance = service.create(
            AcceptanceCreateInput(
                accepted_at=parse_datetime(date),
                company=company,
                plate=plate,
                material_id=material_id,
                quantity=Decimal(quantity),
                note=note,
            ),
            actor_role=x_role,
        )
    except AcceptanceAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except AcceptanceValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"id": acceptance.id, "status": "created"}


@router.get("/acceptance/new", response_class=HTMLResponse)
def acceptance_new_form() -> str:
    return """
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>New Acceptance</title>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
</head>
<body class='bg-light'>
<div class='container py-4'>
  <h1 class='mb-4'>Create Acceptance (IN)</h1>
  <form method='post' action='/acceptance' class='card card-body shadow-sm'>
    <div class='row g-3'>
      <div class='col-md-4'><label class='form-label'>Date</label><input name='date' type='datetime-local' class='form-control' required></div>
      <div class='col-md-4'><label class='form-label'>Company</label><input name='company' class='form-control'></div>
      <div class='col-md-4'><label class='form-label'>Plate</label><input name='plate' class='form-control' required></div>
      <div class='col-md-4'><label class='form-label'>Material ID</label><input name='material_id' type='number' class='form-control' required></div>
      <div class='col-md-4'><label class='form-label'>Quantity (15,3)</label><input name='quantity' type='number' step='0.001' class='form-control' required></div>
      <div class='col-md-12'><label class='form-label'>Note</label><textarea name='note' class='form-control'></textarea></div>
    </div>
    <div class='mt-3'>
      <small class='text-muted'>Send role in header: <code>X-Role: ACCEPTANCE</code> or <code>X-Role: ADMIN</code></small><br>
      <button type='submit' class='btn btn-primary mt-2'>Save Acceptance</button>
    </div>
  </form>
</div>
</body>
</html>
"""


@router.get("/acceptance", response_class=HTMLResponse)
def acceptance_list(session: Session = Depends(get_session)) -> str:
    service = AcceptanceService(session)
    rows = service.list_latest(limit=50)

    body_rows = "".join(
        f"<tr><td>{r.id}</td><td>{r.accepted_at}</td><td>{r.company or ''}</td><td>{r.plate}</td><td>{r.material_id}</td><td>{r.quantity}</td><td>{r.note or ''}</td></tr>"
        for r in rows
    )

    return f"""
<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Acceptance List</title>
  <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
</head>
<body class='bg-light'>
<div class='container py-4'>
  <div class='d-flex justify-content-between align-items-center mb-3'>
    <h1 class='mb-0'>Last 50 Acceptance Entries</h1>
    <a href='/acceptance/new' class='btn btn-primary'>New</a>
  </div>
  <div class='table-responsive card shadow-sm'>
    <table class='table table-striped mb-0'>
      <thead><tr><th>ID</th><th>Date</th><th>Company</th><th>Plate</th><th>Material</th><th>Quantity</th><th>Note</th></tr></thead>
      <tbody>{body_rows}</tbody>
    </table>
  </div>
</div>
</body>
</html>
"""
