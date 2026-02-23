"""Corporate stock table routes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from yem_sistem.db.session import get_session
from yem_sistem.materials.models import Material
from yem_sistem.stock_movements.models import MovementType, StockMovement

router = APIRouter(tags=["stocks"])
templates = Jinja2Templates(directory="src/yem_sistem/web/templates")


@router.get("/stocks", response_class=HTMLResponse)
def stocks_page(
    request: Request,
    q: str = Query(default=""),
    only_critical: int = Query(default=0),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    signed_quantity = case(
        (StockMovement.movement_type == MovementType.IN, StockMovement.quantity),
        (StockMovement.movement_type == MovementType.OUT_PRODUCTION, -StockMovement.quantity),
        (StockMovement.movement_type == MovementType.OUT_CORRECTION, -StockMovement.quantity),
        (StockMovement.movement_type == MovementType.ADJUSTMENT, StockMovement.quantity),
        else_=Decimal("0.000"),
    )

    stock_expr = func.coalesce(func.sum(signed_quantity), Decimal("0.000"))
    stmt = (
        select(
            Material.id.label("material_id"),
            Material.name.label("material_name"),
            stock_expr.label("current_stock_kg"),
            func.max(StockMovement.movement_at).label("last_movement_at"),
        )
        .select_from(Material)
        .outerjoin(StockMovement, StockMovement.material_id == Material.id)
        .group_by(Material.id, Material.name)
    )

    if q.strip():
        stmt = stmt.where(Material.name.ilike(f"%{q.strip()}%"))

    # If project has no critical_level field, ignore this filter as requested.
    critical_col = getattr(Material, "critical_level", None)
    if only_critical == 1 and critical_col is not None:
        stmt = stmt.having(stock_expr <= critical_col)

    rows = session.execute(stmt.order_by(Material.name.asc())).all()

    return templates.TemplateResponse(
        request=request,
        name="stocks.html",
        context={
            "rows": rows,
            "q": q,
            "only_critical": only_critical,
        },
    )
