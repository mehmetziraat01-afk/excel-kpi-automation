"""Corporate dashboard and stock pages."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, cast, Date, func, select
from sqlalchemy.orm import Session

from yem_sistem.db.session import get_session
from yem_sistem.materials.models import Material
from yem_sistem.production_batches.models import BatchStatus, ProductionBatch
from yem_sistem.stock_movements.models import MovementType, StockMovement

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _stock_subquery():
    incoming = case((StockMovement.movement_type == MovementType.IN, StockMovement.quantity), else_=Decimal("0.000"))
    outgoing = case(
        (
            StockMovement.movement_type.in_([MovementType.OUT_PRODUCTION, MovementType.OUT_CORRECTION]),
            StockMovement.quantity,
        ),
        else_=Decimal("0.000"),
    )

    return (
        select(
            StockMovement.material_id.label("material_id"),
            (func.coalesce(func.sum(incoming), Decimal("0.000")) - func.coalesce(func.sum(outgoing), Decimal("0.000"))).label(
                "current_stock_kg"
            ),
            func.max(StockMovement.movement_at).label("last_movement_at"),
        )
        .group_by(StockMovement.material_id)
        .subquery()
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    stock_sq = _stock_subquery()

    stock_by_material = session.execute(
        select(
            Material.name.label("material_name"),
            func.coalesce(stock_sq.c.current_stock_kg, Decimal("0.000")).label("current_stock_kg"),
        )
        .outerjoin(stock_sq, stock_sq.c.material_id == Material.id)
        .order_by(Material.name.asc())
    ).all()

    total_stock_kg = sum((row.current_stock_kg for row in stock_by_material), Decimal("0.000"))

    today = date.today()
    today_in_kg = session.execute(
        select(func.coalesce(func.sum(StockMovement.quantity), Decimal("0.000"))).where(
            StockMovement.movement_type == MovementType.IN,
            cast(StockMovement.movement_at, Date) == today,
        )
    ).scalar_one()

    today_out_production_kg = session.execute(
        select(func.coalesce(func.sum(StockMovement.quantity), Decimal("0.000"))).where(
            StockMovement.movement_type == MovementType.OUT_PRODUCTION,
            cast(StockMovement.movement_at, Date) == today,
        )
    ).scalar_one()

    suspicious_batches_count = session.execute(
        select(func.count(ProductionBatch.id)).where(ProductionBatch.status == BatchStatus.SUSPICIOUS)
    ).scalar_one()

    context = {
        "request": request,
        "page_title": "Dashboard",
        "total_stock_kg": total_stock_kg,
        "today_in_kg": today_in_kg,
        "today_out_production_kg": today_out_production_kg,
        "suspicious_batches_count": suspicious_batches_count,
        "stock_by_material": stock_by_material,
    }
    return templates.TemplateResponse("dashboard.html", context)


@router.get("/stocks", response_class=HTMLResponse)
def stocks_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    stock_sq = _stock_subquery()

    stocks = session.execute(
        select(
            Material.name.label("material_name"),
            func.coalesce(stock_sq.c.current_stock_kg, Decimal("0.000")).label("current_stock_kg"),
            stock_sq.c.last_movement_at,
        )
        .outerjoin(stock_sq, stock_sq.c.material_id == Material.id)
        .order_by(Material.name.asc())
    ).all()

    return templates.TemplateResponse(
        "stocks.html",
        {
            "request": request,
            "page_title": "Stocks",
            "stocks": stocks,
        },
    )
