"""Web application entrypoint."""

from fastapi import FastAPI

from yem_sistem.acceptance.routes import router as acceptance_router
from yem_sistem.imports.routes import router as imports_router
from yem_sistem.production_batches.routes import router as production_batches_router
from yem_sistem.web.routes import router as web_router

app = FastAPI(title="yem_sistem")
app.include_router(acceptance_router)
app.include_router(imports_router)
app.include_router(production_batches_router)

app.include_router(web_router)
