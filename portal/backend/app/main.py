from fastapi import FastAPI

app = FastAPI(title="DreamDocs Academy Portal")

@app.get("/")
def read_root():
    return {"message": "DreamDocs Academy Portal API"}
