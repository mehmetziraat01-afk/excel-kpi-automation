"""Web application entrypoint."""

from fastapi import FastAPI

from yem_sistem.acceptance.routes import router as acceptance_router
from yem_sistem.analysis.routes import router as analysis_router
from yem_sistem.dashboard.routes import router as dashboard_router
from yem_sistem.imports.routes import router as imports_router
from yem_sistem.production_batches.routes import router as production_batches_router
from yem_sistem.stocks.routes import router as stocks_router

app = FastAPI(title="yem_sistem")
app.include_router(acceptance_router)
app.include_router(analysis_router)
app.include_router(dashboard_router)
app.include_router(imports_router)
app.include_router(production_batches_router)
app.include_router(stocks_router)
