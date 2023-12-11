from uvicorn import run
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from routes.routes import app
from sqlalchemy.orm import Session

Base = declarative_base()

from models.models import *

DATABASE_URL = "mysql+pymysql://root:nasm@localhost:3306/fastdb"
engine = create_engine(DATABASE_URL)

Base.metadata.create_all(engine)

application = FastAPI()
application.include_router(app)
