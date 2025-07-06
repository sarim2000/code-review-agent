"""Main FastAPI application"""
from fastapi import FastAPI
from app.api.endpoints import router


app = FastAPI(
    title="Code Review Agent",
    description="Autonomous code review agent system for GitHub PRs",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Code Review Agent API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
