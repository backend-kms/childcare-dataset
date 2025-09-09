# Third-party Libraries
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local Application Modules
from app import model
from app.service import dashboard
from app.utils import ResponseAnnotationHandler, get_db

router = APIRouter()