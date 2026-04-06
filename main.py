# RAG 시스템 메인 파일
# FastAPI 서버 및 라우터 연결

from fastapi import FastAPI
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routers.rag_router import router as rag_router
from routers.search_router import router as search_router

app = FastAPI(
    title="RAG System API", 
    version="1.0.0",
    description="RAG(Retrieval-Augmented Generation) 시스템 API"
)

# 라우터 등록 (컨트롤러 계층 제거)
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
            "rag_status": "/api/rag/",
            "search_query": "/api/search/",
            "embedding_health": "/api/search/health",
            "documents_list": "/api/search/documents",
            "load_documents": "/api/rag/documents",
            "reload_documents": "/api/rag/documents/reload",
            "clear_documents": "/api/rag/documents",
            "docs": "/docs",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    from config import settings
    
    uvicorn.run(
        app, 
        host=settings.host, 
        port=8000,
        reload=settings.debug
    )