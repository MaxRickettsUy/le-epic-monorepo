from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.band.routes import router as band_router
from app.release.routes import router as release_router
from app.settings import settings
from app.track.routes import router as track_router

app = FastAPI(title="le-epic-backend", version="0.2.0")

origins = (
    ["*"]
    if settings.cors_origins == "*"
    else [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
)
allow_credentials = origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(band_router, prefix="/band", tags=["band"])
app.include_router(release_router, prefix="/release", tags=["release"])
app.include_router(track_router, prefix="/track", tags=["track"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
