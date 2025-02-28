from fastapi import FastAPI
from dotenv import load_dotenv
from routers import api_router

load_dotenv()

app = FastAPI(
    title="Posey Voyager",
    description="Web Navigation and Data Collection Service for Posey AI",
    version="0.1.0"
)

app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
