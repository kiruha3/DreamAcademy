from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .courses import router as courses_router
from .invite import router as invite_router

app = FastAPI(title="DreamDocs Academy Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses_router)
app.include_router(invite_router)

@app.get("/")
def read_root():
    return {"message": "DreamDocs Academy Portal API"}
