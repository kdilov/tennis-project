from fastapi import FastAPI
from app.routers.rankings import router

app = FastAPI()

app.include_router(router)