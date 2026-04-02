# RAG 시스템 메인 파일
# FastAPI 서버 및 컨트롤러 연결

from fastapi import FastAPI
from controllers import rag_router, search_router

app = FastAPI(
    title="RAG System API", 
    version="1.0.0",
    description="RAG(Retrieval-Augmented Generation) 시스템 API"
)

# 컨트롤러 라우터 등록
app.include_router(rag_router)
app.include_router(search_router)

@app.get("/")
async def root():
    """기본 엔드포인트"""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "rag_management": "/api/rag",
            "search": "/api/search",
            "docs": "/docs",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """상태 확인 엔드포인트"""
    return {"status": "healthy", "service": "RAG System"}

if __name__ == "__main__":
    import uvicorn
    from config import settings
    
    uvicorn.run(
        app, 
        host=settings.host, 
        port=8000,
        reload=settings.debug
    )