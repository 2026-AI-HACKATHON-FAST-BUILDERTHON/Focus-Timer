"""
Focus Timer - FastAPI Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from routers import auth, sessions, recommendation, report, achievements, survey, analytics

# 앱 생성
app = FastAPI(
    title="Focus Timer API",
    description="집중하지 못하는 당신을 위한 AI 타이머",
    version="1.0.0",
)

# CORS 설정
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(recommendation.router)
app.include_router(report.router)
app.include_router(achievements.router)
app.include_router(survey.router)
app.include_router(analytics.router)


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "focus-timer-api"}


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Focus Timer API",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
