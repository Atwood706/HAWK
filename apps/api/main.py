from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.config import DATA_ROOT
from apps.api.routes import profiles, settings, skills, tools, workflows
from apps.api.seed import ensure_seed_data
from apps.api.storage import FileStore


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_seed_data(FileStore(DATA_ROOT))
    yield


app = FastAPI(title="HAWK Local Workbench API", lifespan=lifespan)
app.include_router(workflows.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
