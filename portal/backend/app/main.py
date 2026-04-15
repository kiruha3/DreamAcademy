from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .courses import router as courses_router
from .invite import router as invite_router
from .auth_router import router as auth_router
from .my_courses import router as my_courses_router
from .admin import router as admin_router
from .course_builder import router as course_builder_router
from .course_content import router as course_content_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DreamDocs Academy Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(invite_router)
app.include_router(my_courses_router)
app.include_router(admin_router)
app.include_router(course_builder_router)
app.include_router(course_content_router)

@app.get("/")
def read_root():
    return {"message": "DreamDocs Academy Portal API"}
