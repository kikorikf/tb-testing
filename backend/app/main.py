from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.scheduler import start_scheduler
from app.routers import approvals, me, permits, questions, test, wfm


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(title="ТБ-Допуск API", version="1.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me.router, prefix="/api/v1")
app.include_router(test.router, prefix="/api/v1")
app.include_router(approvals.router, prefix="/api/v1")
app.include_router(permits.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(wfm.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
