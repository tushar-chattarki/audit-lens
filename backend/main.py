from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import review

app = FastAPI(
    title="Audit Lens — Banking Financial Statement Review Automation API",
    description="FastAPI Backend Orchestrator for Audit Lens (WP-514 Working Paper Engine)",
    version="1.0.0"
)

# Enable CORS for React Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review.router)

@app.get("/")
def root():
    return {
        "service": "Banking Financial Statement Review Automation Backend",
        "status": "HEALTHY",
        "version": "1.0.0",
        "standard": "WP-514 Working Paper"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
