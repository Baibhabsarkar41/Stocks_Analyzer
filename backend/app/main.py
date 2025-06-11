from fastapi import FastAPI
from api.auth import auth_router
from api.endpoints import api_router
from api.search_symbol import sym_router
from fastapi.middleware.cors import CORSMiddleware

from api.scraper import router

app = FastAPI()

origins = [
    "http://localhost:3000",  # React dev server
    # Add other origins as needed, e.g. for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allows your frontend origin
    allow_credentials=True,         # Allows cookies, Authorization headers, etc.
    allow_methods=["*"],            # Allows all HTTP methods
    allow_headers=["*"],            # Allows all headers
)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(api_router, prefix="/api", tags=["api"])
app.include_router(router, prefix="/api", tags=["scraper"])
app.include_router(sym_router)

