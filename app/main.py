from fastapi import FastAPI,Request
import logging
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.rankings import router as rankings_router
from app.routers.health import router as health_router
from app.exceptions import RankingsAPIError
from mangum import Mangum

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()


allowed_origins = [
    "http://localhost:3000",      
    "http://127.0.0.1:3000", 
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rankings_router)
app.include_router(health_router)

@app.exception_handler(RankingsAPIError)
async def rankings_api_error_handler(request: Request, exc: RankingsAPIError):
    return JSONResponse(
        status_code=503,
        content={"error": "External API Error",
                 "detail": exc.message,
                 "args": exc.args},
    )

handler = Mangum(app)
