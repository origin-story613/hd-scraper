from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.deals import router as deals_router
from app.db import init_db

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Home Depot Discount Finder")


@app.on_event("startup")
def _startup() -> None:
    init_db()


app.include_router(deals_router)

# Serve the frontend (index.html, styles.css, app.js) at "/".
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
