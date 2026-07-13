from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from backend.database.mongo import db

from backend.repositories.counter_repository import counter_repository
from backend.repositories.customer_repository import customer_repository
from backend.repositories.company_repository import company_repository
from backend.repositories.import_job_repository import import_job_repository
from backend.database.seeder import seed_masters
from backend.routes.dropdown import router as dropdown_router
from backend.routes.master import router as master_router
from fastapi.middleware.cors import CORSMiddleware

from backend.repositories.import_workflow_repository import (
    import_workflow_repository,
)
from backend.repositories.import_workflow_history_repository import (
    import_workflow_history_repository,
)
from backend.repositories.cfs_repository import cfs_repository
from backend.repositories.transporter_repository import (
    transporter_repository,
)
from backend.repositories.other_gov_agency_type_repository import (
    other_gov_agency_type_repository,
)

from backend.routes.auth import router as auth_router
from backend.routes.company import router as company_router
from backend.routes.customer import router as customer_router
from backend.routes.import_job import router as import_job_router
from backend.routes.import_workflow import router as import_workflow_router
from backend.routes.import_workflow_history import (
    router as import_workflow_history_router,
)
from backend.routes.cfs import router as cfs_router
from backend.routes.transporter import router as transporter_router
from backend.routes.other_gov_agency_type import (
    router as other_gov_agency_type_router,
)

from backend.utils.dependencies import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):

    # customer_repository.create_indexes()
    # company_repository.create_indexes()

    counter_repository.initialize("customer")
    counter_repository.initialize("company")
    counter_repository.initialize("import_job")

    import_job_repository.create_indexes()
    import_workflow_repository.create_indexes()
    import_workflow_history_repository.create_indexes()

    cfs_repository.create_indexes()
    transporter_repository.create_indexes()
    other_gov_agency_type_repository.create_indexes()

    seed_masters()

    yield


app = FastAPI(
    title="Octopus SCM API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://octopus-scm-frontend.vercel.app",
        "https://octopus-scm-frontend-9dw66gi3f-octopus14.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(company_router)

app.include_router(import_job_router)
app.include_router(import_workflow_router)
app.include_router(import_workflow_history_router)

app.include_router(cfs_router)
app.include_router(transporter_router)
app.include_router(other_gov_agency_type_router)
app.include_router(dropdown_router)
app.include_router(master_router)

@app.get("/")
def root():
    return {
        "message": "Octopus SCM API is running",
        "database": db.name,
    }


@app.get("/me")
def me(user=Depends(get_current_user)):
    return user
