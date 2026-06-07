from fastapi import FastAPI

app = FastAPI(title="TutorIA API")

@app.get("/")
def root():
    return {"status": "ok", "message": "TutorIA backend corriendo"}