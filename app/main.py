from fastapi import FastAPI
from app.api.v1.endpoints import router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="AI News Research and Idea Generator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Backend running successfully!"}
