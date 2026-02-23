"""Import HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from yem_sistem.db.session import get_session
from yem_sistem.imports.dtm_batch_import import DtmBatchImportService, DtmImportError

router = APIRouter(tags=["imports"])


@router.post("/imports/dtm/batch")
async def import_dtm_batch(
    file: UploadFile = File(...),
    x_role: str = Header(default="", alias="X-Role"),
    session: Session = Depends(get_session),
) -> dict:
    service = DtmBatchImportService(session)
    try:
        summary = service.import_file(file_name=file.filename or "", content=await file.read(), actor_role=x_role)
        return {
            "rows_processed": summary.rows_processed,
            "movements_created": summary.movements_created,
            "suspicious_batches_count": summary.suspicious_batches_count,
        }
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except DtmImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
