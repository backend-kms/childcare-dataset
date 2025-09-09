# Third-party Libraries
from debug_toolbar.middleware import DebugToolbarMiddleware
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination
from fastapi_pagination.utils import disable_installed_extensions_check
from pydantic import BaseModel

# Local Application Modules
import config

app = FastAPI(
    title="Thesis API",
    description="",
    version="1.0.0",
    debug=config.DEBUG,
)

disable_installed_extensions_check()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.add_middleware(
    DebugToolbarMiddleware,
    panels=["debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel"],
)

# app.include_router(user.router, prefix="/api/v1/user")

add_pagination(app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    custom_errors = []
    for err in exc.errors():
        custom_errors.append(
            {
                "loc": err["loc"],
                "msg": err["msg"],
                "type": err["type"],
            }
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": custom_errors},
    )

